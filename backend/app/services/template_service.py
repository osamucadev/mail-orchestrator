from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.template import Template
from app.models.template_placeholder import TemplatePlaceholder

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def _title_from_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def parse_placeholders(*texts: str | None) -> list[dict]:
    """
    Extract placeholders from any number of template strings.

    Returns a list of dicts like:
    { "key": "company", "label": "Company", "order_index": 0 }
    """
    order: list[str] = []
    seen: set[str] = set()

    for text in texts:
        if not text:
            continue
        for match in PLACEHOLDER_RE.finditer(text):
            key = match.group(1)
            if key not in seen:
                seen.add(key)
                order.append(key)

    result: list[dict] = []
    for idx, key in enumerate(order):
        result.append(
            {
                "key": key,
                "label": _title_from_key(key),
                "order_index": idx,
            }
        )
    return result


def _sync_placeholders(db: Session, template: Template) -> None:
    parsed = parse_placeholders(
        template.subject_template,
        template.body_text_template,
        template.body_html_template,
    )

    db.execute(
        select(TemplatePlaceholder).where(TemplatePlaceholder.template_id == template.id)
    )
    # Delete existing placeholders and re-create based on current content
    db.query(TemplatePlaceholder).filter(TemplatePlaceholder.template_id == template.id).delete()

    for item in parsed:
        db.add(
            TemplatePlaceholder(
                template_id=template.id,
                key=item["key"],
                label=item["label"],
                order_index=item["order_index"],
            )
        )


def list_templates(db: Session) -> list[Template]:
    stmt = select(Template).order_by(Template.id.desc())
    return list(db.scalars(stmt).all())


def get_template(db: Session, template_id: int) -> Template | None:
    return db.get(Template, template_id)


def create_template(db: Session, data: dict) -> Template:
    template = Template(**data)
    db.add(template)
    db.commit()
    db.refresh(template)

    _sync_placeholders(db, template)
    db.commit()
    db.refresh(template)

    return template


def update_template(db: Session, template_id: int, data: dict) -> Template | None:
    template = get_template(db, template_id)
    if template is None:
        return None

    for key, value in data.items():
        setattr(template, key, value)

    db.commit()
    db.refresh(template)

    _sync_placeholders(db, template)
    db.commit()
    db.refresh(template)

    return template


def delete_template(db: Session, template_id: int) -> bool:
    template = get_template(db, template_id)
    if template is None:
        return False

    db.delete(template)
    db.commit()
    return True


def list_placeholders(db: Session, template_id: int) -> list[TemplatePlaceholder] | None:
    template = get_template(db, template_id)
    if template is None:
        return None

    stmt = (
        select(TemplatePlaceholder)
        .where(TemplatePlaceholder.template_id == template_id)
        .order_by(TemplatePlaceholder.order_index.asc())
    )
    return list(db.scalars(stmt).all())
