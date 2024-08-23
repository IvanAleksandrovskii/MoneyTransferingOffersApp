from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from fastapi_storages.integrations.sqlalchemy import FileType

from core import storage
from core.models import Base


class TransferProvider(Base):
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    logo = mapped_column(FileType(storage=storage))

    exchange_rates = relationship("ProviderExchangeRate", back_populates="provider", cascade="all, delete-orphan")
    transfer_rules = relationship("TransferRule", back_populates="provider", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return f"{self.name} ({self.url})"

    def __repr__(self) -> str:
        return f"<TransferProvider(id={self.id}, name={self.name})>"
