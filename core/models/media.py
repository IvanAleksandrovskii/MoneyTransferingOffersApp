# core/models/media.py

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_storages.integrations.sqlalchemy import FileType

from .base import Base
from .media_to_text import text_media_association
from core.fastapi_storage import bot_storage

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .text import Text


class Media(Base):
    __tablename__ = 'media'

    file: Mapped[str] = mapped_column(FileType(storage=bot_storage))

    file_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    # Many-to-many relationship with Text
    texts: Mapped[list["Text"]] = relationship(
        "Text",
        secondary=text_media_association,
        back_populates="media_files",
        cascade="all, delete",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Media(id={self.id}, file_type={self.file_type})>"
