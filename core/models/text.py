# core/models/text.py

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .media_to_text import text_media_association

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .media import Media


class Text(Base):
    # How I will call this text
    context_marker: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)

    body: Mapped[str] = mapped_column(String, nullable=False)  

    is_default_media: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    reading_pagination: Mapped[int] = mapped_column(nullable=True)

    media_files: Mapped[list["Media"]] = relationship(
        "Media",
        secondary=text_media_association,
        back_populates="texts",
        cascade="all, delete",
        passive_deletes=True
    )
