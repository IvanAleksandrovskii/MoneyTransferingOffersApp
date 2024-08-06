from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base


class Currency(Base):
    # TODO: with my naming logic still need to write down the name if it ends with "ies" in multiple form
    __tablename__ = "currencies"

    # TODO: decide if we should keep more than one language (?)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Example: US Dollar, Euro, Russian Ruble etc.
    symbol: Mapped[str] = mapped_column(String, nullable=True)  # Example: $, £, €, UTF-8
    abbreviation: Mapped[str] = mapped_column(String, nullable=False)  # Example: USD, EUR, RUB etc.

    countries = relationship("Country", back_populates="local_currency")

    __table_args__ = (
        UniqueConstraint('abbreviation', name='uq_currency_abbreviation'),
    )

    def __repr__(self) -> str:
        return "<Currency(id=%s, abbreviation=%s)>" % (self.id, self.abbreviation)
