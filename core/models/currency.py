from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base


class Currency(Base):
    __tablename__ = "currencies"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Example: US Dollar, Euro, Russian Ruble etc.
    symbol: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Example: $, £, €, UTF-8
    abbreviation: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Example: USD, EUR, RUB etc.

    countries = relationship("Country", back_populates="local_currency", lazy="noload")

    __table_args__ = (
        UniqueConstraint('abbreviation', name='uq_currency_abbreviation'),
    )

    def __str__(self):
        return f"{self.abbreviation} ({self.name} - {self.symbol})"

    def __repr__(self) -> str:
        return "<Currency(id=%s, abbreviation=%s)>" % (self.id, self.abbreviation)
