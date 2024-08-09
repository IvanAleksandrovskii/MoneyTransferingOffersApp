from typing import Optional
import uuid

from sqlalchemy import ForeignKey, Float, String, Index, CheckConstraint, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models.country import Country
from core.models.currency import Currency
from core.models.transfer_provider import TransferProvider


# Middle-layer table for many-to-many relationship between TransferRule and Document
transfer_rule_documents = Table(
    'transfer_rule_documents',
    Base.metadata,
    Column('transfer_rule_id', ForeignKey('transfer_rules.id'), primary_key=True),
    Column('document_id', ForeignKey('documents.id'), primary_key=True)
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
    estimated_transfer_time: Mapped[Optional[str]] = mapped_column(String,
                                                                   nullable=True)  # Time transfer takes: hours/days etc.
    #                                                        TODO: nullable=False (?) for estimated_transfer_time
    # required_documents: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # TODO: nullable=False (!)

    required_documents = relationship("Document", secondary=transfer_rule_documents,
                                      back_populates="transfer_rules", lazy="selectin")

    # TODO: New estimate time logic
    # min_execution_time = Column(DateTime, nullable=False)
    # max_execution_time = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_transfer_rule_send_country', 'send_country_id'),
        Index('idx_transfer_rule_receive_country', 'receive_country_id'),
        Index('idx_transfer_rule_provider', 'provider_id'),
        Index('idx_transfer_rule_currency', 'transfer_currency_id'),
        CheckConstraint('min_transfer_amount <= max_transfer_amount', name='check_min_max_transfer_amount'),
        CheckConstraint('fee_percentage >= 0 AND fee_percentage < 100', name='check_fee_percentage_range'),
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
