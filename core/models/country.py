import uuid

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base


class Country(Base):
    # TODO: with my naming logic still need to write down the name if it ends with "ies" in multiple form
    __tablename__ = "countries"

    name: Mapped[str] = mapped_column(String, nullable=False)

    local_currency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("currencies.id"), nullable=False)
    local_currency = relationship("Currency", back_populates="countries")

    def __repr__(self) -> str:
        return "<Country(id=%s, name=%s, local_currency_id=%s)>" % (self.id, self.name, self.local_currency_id)
