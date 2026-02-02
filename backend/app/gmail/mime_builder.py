from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from email.message import EmailMessage
from email.utils import formatdate


def _split_mime(mime_type: str) -> tuple[str, str]:
    if "/" not in mime_type:
        return "application", "octet-stream"
    return tuple(mime_type.split("/", 1))  # type: ignore[return-value]


def build_email_message(
    *,
    to: str,
    subject: str,
    body_text: str | None,
    body_html: str | None,
    attachments: list[dict[str, Any]] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    text = body_text or ""
    html = body_html or ""

    msg.set_content(text)

    if html.strip():
        msg.add_alternative(html, subtype="html")

    inline_items: list[dict[str, Any]] = []
    normal_items: list[dict[str, Any]] = []

    for a in attachments or []:
        disposition = (a.get("disposition") or "").strip().lower()
        storage_path = (a.get("storage_path") or "").strip()

        if not storage_path or storage_path == "pending":
            continue

        path = Path(storage_path)
        if not path.exists() or not path.is_file():
            continue

        item = dict(a)
        item["storage_path"] = str(path)

        if disposition == "inline":
            inline_items.append(item)
        else:
            normal_items.append(item)

    # Inline images must be RELATED to the HTML part to render with cid: references
    if inline_items and html.strip():
        html_part = msg.get_body(preferencelist=("html",))
        if html_part is not None:
            for a in inline_items:
                path = Path(a["storage_path"])
                filename = a.get("filename") or path.name
                mime_type = a.get("mime_type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
                maintype, subtype = _split_mime(mime_type)
                content_id = (a.get("content_id") or "").strip()

                data = path.read_bytes()

                # EmailMessage will set Content-ID when cid is provided
                html_part.add_related(
                    data,
                    maintype=maintype,
                    subtype=subtype,
                    cid=f"<{content_id}>",
                    filename=filename,
                    disposition="inline",
                )

    # Normal attachments go to the root message
    for a in normal_items:
        path = Path(a["storage_path"])
        filename = a.get("filename") or path.name
        mime_type = a.get("mime_type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        maintype, subtype = _split_mime(mime_type)

        data = path.read_bytes()

        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=filename,
            disposition="attachment",
        )

    return msg
