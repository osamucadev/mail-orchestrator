from __future__ import annotations

import enum


class RespondedSource(str, enum.Enum):
    gmail = "gmail"
    manual = "manual"


class AttachmentDisposition(str, enum.Enum):
    attachment = "attachment"
    inline = "inline"
