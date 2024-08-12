from datetime import timedelta
from typing import Optional
import uuid

from sqlalchemy import (
    ForeignKey, Float, String, Index,
    CheckConstraint, Table, Column, Interval,
    Integer, UniqueConstraint, UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from core.models import Base
from core.models.country import Country
from core.models.currency import Currency
from core.models.transfer_provider import TransferProvider


# Middle-layer table for many-to-many relationship between TransferRule and Document
# transfer_rule_documents = Table(
#     'transfer_rule_documents',
#     Base.metadata,
#     Column('transfer_rule_id', ForeignKey('transfer_rules.id')),
#     Column('document_id', ForeignKey('documents.id')),
#     PrimaryKeyConstraint('transfer_rule_id', 'document_id', name='pk_transfer_rule_document')
# )
transfer_rule_documents = Table(
    'transfer_rule_documents',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('transfer_rule_id', UUID(as_uuid=True), ForeignKey('transfer_rules.id'), nullable=False),
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
)


class TransferRule(Base):
    # TODO: What about adding more fields or improving the structure of this model? (?)
    # TODO: Add methods for business logic, such as calculating fees, validating transfer amounts, etc.
    send_country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"), nullable=False)
    send_country: Mapped[Country] = relationship("Country", foreign_keys=[send_country_id], lazy="joined")

    receive_country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"), nullable=False)
    receive_country: Mapped[Country] = relationship("Country", foreign_keys=[receive_country_id], lazy="joined")

    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_providers.id", ondelete="CASCADE"),
                                                   nullable=False)
    provider: Mapped[TransferProvider] = relationship("TransferProvider", foreign_keys=[provider_id],
                                                      back_populates="transfer_rules", lazy="joined")

    # TODO: nullable=False? or not? could be null if no min or max? should we use default 0 value in that case?
    # TODO: Same about max! What if we don't have max? So some validation errors could occur?
    fee_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    min_transfer_amount: Mapped[float] = mapped_column(Float, nullable=False)  # TODO: nullable=False?
    max_transfer_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=False)  # TODO: nullable=False?

    # Info about transfer currency
    transfer_currency_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("currencies.id"), nullable=False)
    transfer_currency: Mapped[Optional[Currency]] = relationship("Currency", foreign_keys=[transfer_currency_id],
                                                                 lazy="joined")

    # Other fields here... What else can we add here? I mean, if we need it
    # Online / Office
    # Time transfer takes
    # Documents needed
    transfer_method: Mapped[str] = mapped_column(String, nullable=False)  # Online / Office TODO: maybe enum or binary?
    # estimated_transfer_time: Mapped[Optional[str]] = mapped_column(String,
    #                                                                nullable=True)  # Time transfer takes: hours/days etc.
    #                                                        TODO: nullable=False (?) for estimated_transfer_time
    min_transfer_time: Mapped[timedelta] = mapped_column(Interval, nullable=False)
    max_transfer_time: Mapped[timedelta] = mapped_column(Interval, nullable=False)

    # required_documents: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # TODO: nullable=False (!)

    required_documents = relationship("Document", secondary=transfer_rule_documents,
                                      back_populates="transfer_rules", lazy="selectin")

    __table_args__ = (
        Index('idx_transfer_rule_send_country', 'send_country_id'),
        Index('idx_transfer_rule_receive_country', 'receive_country_id'),
        Index('idx_transfer_rule_provider', 'provider_id'),
        Index('idx_transfer_rule_currency', 'transfer_currency_id'),
        CheckConstraint('min_transfer_amount <= max_transfer_amount', name='check_min_max_transfer_amount'),
        CheckConstraint('fee_percentage >= 0 AND fee_percentage < 100', name='check_fee_percentage_range'),
        UniqueConstraint('send_country_id', 'receive_country_id', 'provider_id', 'transfer_currency_id',
                         name='uq_transfer_rule_unique_combination'),
    )

    # TODO: Add more validation (?)
    @validates('fee_percentage', 'min_transfer_amount', 'max_transfer_amount')
    def validate_fields(self, key, value):
        if key == 'fee_percentage' and (value < 0 or value > 100):
            raise ValueError('fee_percentage must be between 0 and 100')
        if key in ['min_transfer_amount', 'max_transfer_amount'] and value < 0:
            raise ValueError(f'{key} must be non-negative')
        if key == 'max_transfer_amount' and hasattr(self, 'min_transfer_amount') and value < self.min_transfer_amount:
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
