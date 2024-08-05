import uuid

from sqlalchemy import MetaData, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

from core import settings
from utils import camel_case_to_snake_case


metadata = MetaData(naming_convention=settings.db.naming_convention)


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = metadata

    @declared_attr
    def __tablename__(cls) -> str:
        return f"{camel_case_to_snake_case(cls.__name__)}s"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
