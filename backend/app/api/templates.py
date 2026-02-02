from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate
from app.schemas.template_placeholder import TemplatePlaceholderRead
from app.services.template_service import (
    create_template,
    delete_template,
    get_template,
    list_placeholders,
    list_templates,
    update_template,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateRead])
def read_templates(db: Session = Depends(get_db)):
    return list_templates(db)


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def write_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    return create_template(db, payload.model_dump())


@router.get("/{template_id}", response_model=TemplateRead)
def read_template(template_id: int, db: Session = Depends(get_db)):
    template = get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=TemplateRead)
def edit_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)):
    template = update_template(db, template_id, payload.model_dump())
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_template(template_id: int, db: Session = Depends(get_db)):
    ok = delete_template(db, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return None


@router.get("/{template_id}/placeholders", response_model=list[TemplatePlaceholderRead])
def read_placeholders(template_id: int, db: Session = Depends(get_db)):
    items = list_placeholders(db, template_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return items
