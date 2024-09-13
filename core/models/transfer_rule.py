from datetime import timedelta
from typing import Optional
import uuid

from sqlalchemy import (
    ForeignKey, Float, String, Index,
    CheckConstraint, Table, Column, Interval,
    Integer, UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from core.models import Base
from core.models.country import Country
from core.models.currency import Currency
from core.models.transfer_provider import TransferProvider


# Many-to-many relationship between TransferRule and Document middle-layer-table
transfer_rule_documents = Table(
    'transfer_rule_documents',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('transfer_rule_id', UUID(as_uuid=True), ForeignKey('transfer_rules.id', ondelete="CASCADE"), nullable=False),
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id', ondelete="CASCADE"), nullable=False)
)


class TransferRule(Base):
    # Foreign key relationships
    send_country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id", ondelete="CASCADE"), nullable=False)
    send_country: Mapped[Country] = relationship("Country", foreign_keys=[send_country_id], lazy="joined")

    receive_country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id", ondelete="CASCADE"), nullable=False)
    receive_country: Mapped[Country] = relationship("Country", foreign_keys=[receive_country_id], lazy="joined")

    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_providers.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[TransferProvider] = relationship("TransferProvider", foreign_keys=[provider_id],
                                                      back_populates="transfer_rules", lazy="joined")

    # Transfer details
    fee_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    fee_fixed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    min_transfer_amount: Mapped[float] = mapped_column(Float, nullable=False)
    max_transfer_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Transfer currency information
    transfer_currency_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("currencies.id", ondelete="CASCADE"), nullable=False)
    transfer_currency: Mapped[Optional[Currency]] = relationship("Currency", foreign_keys=[transfer_currency_id],
                                                                 lazy="joined")

    # Additional transfer information
    transfer_method: Mapped[str] = mapped_column(String, nullable=False)  # Online / Office / Need to call an operator, etc...

    min_transfer_time: Mapped[timedelta] = mapped_column(Interval, nullable=False)
    max_transfer_time: Mapped[timedelta] = mapped_column(Interval, nullable=False)

    # Many-to-many relationship with Document
    required_documents = relationship("Document", secondary=transfer_rule_documents,
                                      back_populates="transfer_rules", lazy="selectin")

    __table_args__ = (
        # Indexes for improved query performance
        Index('idx_transfer_rule_send_country', 'send_country_id'),
        Index('idx_transfer_rule_receive_country', 'receive_country_id'),
        Index('idx_transfer_rule_provider', 'provider_id'),
        Index('idx_transfer_rule_currency', 'transfer_currency_id'),
        # Constraints to ensure data integrity
        CheckConstraint('min_transfer_amount <= max_transfer_amount', name='check_min_max_transfer_amount'),
        CheckConstraint('fee_percentage >= 0 AND fee_percentage < 100', name='check_fee_percentage_range'),
    )

    @validates('fee_percentage', 'min_transfer_amount', 'max_transfer_amount')
    def validate_fields(self, key, value):
        """
        Validate the fee percentage and transfer amounts to ensure they are within acceptable ranges.
        """
        if key == 'fee_percentage' and (value < 0 or value > 100):
            raise ValueError('fee_percentage must be between 0 and 100')
        elif key == 'fee_fixed' and value is not None:
            if value < 0:
                raise ValueError('fee_fixed must be non-negative')
        if key == 'min_transfer_amount' and value < 0:
            raise ValueError('min_transfer_amount must be non-negative')
        if key == 'max_transfer_amount' and value is not None and value < 0:
            raise ValueError('max_transfer_amount must be non-negative or None')
        if key == 'max_transfer_amount' and value is not None and hasattr(self, 'min_transfer_amount') and self.min_transfer_amount is not None and value < self.min_transfer_amount:
            raise ValueError('max_transfer_amount must be greater than or equal to min_transfer_amount')
        return value

    def __str__(self):
        return (
            f"{self.provider.name}: {self.send_country.abbreviation} -> {self.receive_country.abbreviation} "
            f"({self.transfer_currency.abbreviation}) - {self.min_transfer_amount} to {self.max_transfer_amount}"
        )

    def __repr__(self) -> str:
        return (
            f"<TransferRule("
            f"id={self.id}, "
            f"send_country={self.send_country_id}, "
            f"receive_country={self.receive_country_id}, "
            f"currency={self.transfer_currency_id}, "
            f"provider={self.provider_id}, "
            f"fee_percentage={self.fee_percentage}, "
            f"min_transfer_amount={self.min_transfer_amount}, "
            f"max_transfer_amount={self.max_transfer_amount}, "
            f"is_active={self.is_active}"
            f")>"
        )
