from sqlalchemy import String, event
from sqlalchemy.orm import mapped_column, Mapped, relationship
from fastapi_storages.integrations.sqlalchemy import FileType

from core import storage, logger
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


@event.listens_for(TransferProvider, 'before_update')
def before_update_transfer_provider(mapper, connection, target):
    if hasattr(target, '_logo_to_delete') and target._logo_to_delete:
        try:
            storage.delete(target._logo_to_delete)
        except Exception as e:
            logger.error(f"Error deleting old logo for provider {target.name}: {str(e)}")
        delattr(target, '_logo_to_delete')


@event.listens_for(TransferProvider.logo, 'set')
def on_logo_set(target, value, oldvalue, initiator):
    if oldvalue and oldvalue != value:
        target._logo_to_delete = oldvalue


@event.listens_for(TransferProvider, 'after_delete')
def after_delete_transfer_provider(mapper, connection, target):
    if target.logo:
        try:
            storage.delete(target.logo)
        except Exception as e:
            logger.error(f"Error deleting logo for provider {target.name}: {str(e)}")
