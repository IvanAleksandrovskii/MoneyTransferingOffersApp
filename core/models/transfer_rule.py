import uuid

from sqlalchemy import ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base


class TransferRule(Base):
    # TODO: cannot decide on what do we need here
    send_country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"), nullable=False)
    receive_country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"), nullable=False)
    currency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("currencies.id"), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_providers.id"), nullable=False)

    # TODO: think about it: need to improve, but dk how, keeping it as it is for now
    send_country = relationship("Country", foreign_keys=[send_country_id])
    receive_country = relationship("Country", foreign_keys=[receive_country_id])
    currency = relationship("Currency", foreign_keys=[currency_id])
    provider = relationship("TransferProvider", foreign_keys=[provider_id])

    # TODO: nullable=False? or not? could be null if no min or max? should we use default value in that case?
    fee_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    min_transfer_amount: Mapped[float] = mapped_column(Float, nullable=False)
    max_transfer_amount: Mapped[float] = mapped_column(Float, nullable=True)

    # Other fields here... What else can we add here? I mean, if we need it
    # Online / Office
    # Time transfer takes
    # Documents needed
    transfer_method: Mapped[str] = mapped_column(String, nullable=False)  # Online / Office
    estimated_transfer_time: Mapped[str] = mapped_column(String, nullable=True)  # Time transfer takes: hours/days etc.
    required_documents: Mapped[str] = mapped_column(String, nullable=True)

    def __repr__(self):
        return ("<TransferRule(id=%s, send_country=%s, receive_country=%s, currency=%s, provider=%s, "
                "fee_percentage=%s, min_transfer_amount=%s, max_transfer_amount=%s)>") % (
            self.id,
            self.send_country_id,
            self.receive_country_id,
            self.currency_id,
            self.provider_id,
            self.fee_percentage,
            self.min_transfer_amount,
            self.max_transfer_amount
        )
