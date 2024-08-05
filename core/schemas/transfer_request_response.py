from pydantic import BaseModel, UUID4, Field
from typing import List, Optional


class TransferRequest(BaseModel):
    amount: float = Field(..., gt=0)  # raises ValidationError if amount <= 0
    currency: str
    from_country: str
    to_country: str


class TransferRuleResponse(BaseModel):
    id: UUID4
    transfer_currency: str
    fee_percentage: float
    min_transfer_amount: float
    max_transfer_amount: Optional[float]
    transfer_method: str
    estimated_transfer_time: Optional[str]
    required_documents: Optional[str]
    exchange_rate: float


class ProviderResponse(BaseModel):
    id: UUID4
    name: str
    # TODO: add url logic
    # url: Optional[str]
    transfer_rules: List[TransferRuleResponse]
