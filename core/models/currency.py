from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base


class Currency(Base):
    __tablename__ = "currencies"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Example: US Dollar, Euro, Russian Ruble etc.
    symbol: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Example: $, £, €, UTF-8
    abbreviation: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)  # Example: USD, EUR, RUB etc.

    countries = relationship("Country", back_populates="local_currency",
                             lazy="noload", cascade="all, delete-orphan")

    transfer_rules = relationship("TransferRule", back_populates="transfer_currency", cascade="all, delete-orphan")
    from_exchange_rates = relationship("ProviderExchangeRate", foreign_keys="ProviderExchangeRate.from_currency_id",
                                       back_populates="from_currency", cascade="all, delete-orphan")
    to_exchange_rates = relationship("ProviderExchangeRate", foreign_keys="ProviderExchangeRate.to_currency_id",
                                     back_populates="to_currency", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.abbreviation} ({self.name} - {self.symbol})"

    def __repr__(self) -> str:
        return "<Currency(id=%s, abbreviation=%s)>" % (self.id, self.abbreviation)
