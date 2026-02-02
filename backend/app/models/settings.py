from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    t_white_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    t_blue_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=360)
    t_yellow_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440)
    t_red_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=4320)
