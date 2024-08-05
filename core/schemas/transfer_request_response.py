from pydantic import BaseModel, UUID4, Field
from typing import List, Optional


# TODO: Add validation
class TransferRequest(BaseModel):
    send_country: str
    receive_country: str
    amount: float = Field(..., gt=0)  # raises ValidationError if amount <= 0
    currency: str


class TransferRuleResponse(BaseModel):
    id: UUID4
    send_country: str
    receive_country: str
    transfer_currency: str
    fee_percentage: float
    min_transfer_amount: float
    max_transfer_amount: Optional[float]
    transfer_method: str
    estimated_transfer_time: Optional[str]
    required_documents: Optional[str]
    provider_name: str

    @classmethod
    def from_orm(cls, db_object):
        return cls(
            id=db_object.id,
            send_country=db_object.send_country.name if db_object.send_country else None,
            receive_country=db_object.receive_country.name if db_object.receive_country else None,
            transfer_currency=db_object.transfer_currency.abbreviation if db_object.transfer_currency else None,
            fee_percentage=db_object.fee_percentage,
            min_transfer_amount=db_object.min_transfer_amount,
            max_transfer_amount=db_object.max_transfer_amount,
            transfer_method=db_object.transfer_method,
            estimated_transfer_time=db_object.estimated_transfer_time,
            required_documents=db_object.required_documents,
            provider_name=db_object.provider.name if db_object.provider else None
        )

    class Config:
        from_attributes = True


class ProviderResponse(BaseModel):
    id: UUID4
    name: str
    transfer_rules: List[TransferRuleResponse]

    class Config:
        from_attributes = True

    # TODO: add url logic
    # url: Optional[str]


class TransferResponse(BaseModel):
    source_currency: str
    source_amount: float
    destination_currency: str
    converted_amount: float
    exchange_rate: float
    fee_percentage: float
    fee_amount: float
    transfer_amount: float
    provider: str
    transfer_method: str
    estimated_transfer_time: str
    required_documents: str
