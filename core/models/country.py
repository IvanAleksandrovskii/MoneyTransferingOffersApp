import uuid

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base


class Country(Base):
    __tablename__ = "countries"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    abbreviation: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    local_currency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("currencies.id", ondelete="RESTRICT"),
                                                         nullable=False)
    local_currency = relationship("Currency", back_populates="countries")

    # These relationships are for delete logic
    send_transfer_rules = relationship("TransferRule", foreign_keys="TransferRule.send_country_id",
                                       back_populates="send_country", cascade="all, delete-orphan")
    receive_transfer_rules = relationship("TransferRule", foreign_keys="TransferRule.receive_country_id",
                                          back_populates="receive_country", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

    def __repr__(self) -> str:
        return "<Country(id=%s, name=%s, local_currency_id=%s)>" % (self.id, self.name, self.local_currency_id)
