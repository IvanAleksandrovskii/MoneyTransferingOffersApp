# core/models/button.py

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Button(Base):
    
    context_marker: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    callback_data: Mapped[str] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=True)

    is_half_width: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    order: Mapped[int] = mapped_column(nullable=False, default=0)

    def __str__(self):
        return f"text={self.text}, context_marker={self.context_marker}"

    def __repr__(self):
        return self.__str__()
