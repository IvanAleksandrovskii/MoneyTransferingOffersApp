# core/models/media_to_text.py

from sqlalchemy import Table, Column, ForeignKey, UUID

from .base import Base

# Many-to-many Text and Media
text_media_association = Table(
    'text_media_association',
    Base.metadata,
    Column('text_id', UUID(as_uuid=True), ForeignKey('texts.id', ondelete="CASCADE")),
    Column('media_id', UUID(as_uuid=True), ForeignKey('media.id', ondelete="CASCADE"))
)
