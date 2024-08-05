from pydantic import BaseModel, UUID4, Field
from typing import List, Optional


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

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, db_object):
        return cls(
            id=db_object.id,
            send_country=db_object.send_country.name,
            receive_country=db_object.receive_country.name,
            transfer_currency=db_object.transfer_currency.abbreviation,
            fee_percentage=db_object.fee_percentage,
            min_transfer_amount=db_object.min_transfer_amount,
            max_transfer_amount=db_object.max_transfer_amount,
            transfer_method=db_object.transfer_method,
            estimated_transfer_time=db_object.estimated_transfer_time,
            required_documents=db_object.required_documents,
            provider_name=db_object.provider.name
        )


class ProviderResponse(BaseModel):
    id: UUID4
    name: str
    transfer_rules: List[TransferRuleResponse]

    class Config:
        from_attributes = True

    # TODO: add url logic
    # url: Optional[str]
