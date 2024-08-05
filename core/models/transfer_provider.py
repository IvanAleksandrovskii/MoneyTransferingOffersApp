from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from core.models import Base


class TransferProvider(Base):
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    exchange_rates = relationship("ProviderExchangeRate", back_populates="provider")
    transfer_rules = relationship("TransferRule", back_populates="provider")

    # TODO: think where it should be stored, I mean the link to the provider's source
    # url: Mapped[str] = mapped_column(String, nullable=False)
    # api_key: Mapped[str] = mapped_column(String, nullable=True) # TODO: think about it too, if we need it here or not

    def __repr__(self) -> str:
        return "<TransferProviders(id=%s, name=%s)>" % (self.id, self.name)
