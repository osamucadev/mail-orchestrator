from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from email.message import EmailMessage
from email.utils import formatdate, make_msgid


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

    # Always set a plain text part
    msg.set_content(text)

    # Add HTML alternative if provided
    if html.strip():
        msg.add_alternative(html, subtype="html")

    # Attach files only when a real storage_path exists
    for a in attachments or []:
        disposition = (a.get("disposition") or "").strip().lower()
        storage_path = (a.get("storage_path") or "").strip()

        # Frontend currently sends "pending" because upload is not implemented yet
        if not storage_path or storage_path == "pending":
            continue

        path = Path(storage_path)
        if not path.exists() or not path.is_file():
            continue

        filename = a.get("filename") or path.name
        mime_type = a.get("mime_type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        maintype, subtype = mime_type.split("/", 1) if "/" in mime_type else ("application", "octet-stream")

        data = path.read_bytes()

        if disposition == "inline":
            # Inline attachments require Content-ID and related structure
            # This is simplified: EmailMessage will handle parts, but true inline rendering
            # will be improved when we implement actual inline upload and cid mapping.
            cid = a.get("content_id") or make_msgid(domain="mail-orchestrator.local").strip("<>")
            msg.add_attachment(
                data,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
                disposition="inline",
                cid=f"<{cid}>",
            )
        else:
            msg.add_attachment(
                data,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
                disposition="attachment",
            )

    return msg
