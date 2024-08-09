from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from . import DocumentResponse
from .base import BaseResponse
from .country import CountryResponse
from .currency import CurrencyResponse
from .provider import ProviderResponse


class TransferRuleDetails(BaseModel):
    id: UUID
    provider: ProviderResponse
    transfer_method: str
    estimated_transfer_time: Optional[str] = None  # TODO: update when time field changed
    # min_execution_time: datetime
    # max_execution_time: datetime
    required_documents: List[DocumentResponse]
    original_amount: Optional[float] = Field(None, ge=0)
    converted_amount: Optional[float] = Field(None, ge=0)
    transfer_currency: CurrencyResponse
    amount_received: Optional[float] = Field(None, ge=0)
    transfer_fee: Optional[float] = Field(None, ge=0)
    transfer_fee_percentage: float = Field(..., ge=0, le=100)
    min_transfer_amount: float = Field(..., gt=0)
    max_transfer_amount: float = Field(..., gt=0)
    exchange_rate: Optional[float] = Field(None, gt=0)
    conversion_path: List[str]

    @model_validator(mode='after')
    def validate_transfer_rule_details(self) -> 'TransferRuleDetails':
        # Ensure transfer_fee_percentage is between 0 and 100
        if self.transfer_fee_percentage < 0 or self.transfer_fee_percentage > 100:
            raise ValueError("transfer_fee_percentage must be between 0 and 100")
        # Ensure max_transfer_amount is greater than min_transfer_amount
        if self.max_transfer_amount <= self.min_transfer_amount:
            raise ValueError("max_transfer_amount must be greater than min_transfer_amount")

        # Ensure that optional amounts are positive if provided
        for field_name in ['original_amount', 'converted_amount', 'amount_received', 'transfer_fee', 'exchange_rate']:
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be greater than or equal to 0")

        return self

    model_config = {
        "extra": "forbid",  # This will raise an error if extra fields are provided
    }


class DetailedTransferRuleResponse(BaseResponse):
    provider_name: str
    provider_id: UUID
    provider_url: str | None  # TODO: str only if nullable is False in the model
    send_country_name: str
    send_country_id: UUID
    receive_country_name: str
    receive_country_id: UUID
    transfer_currency_abbreviation: str
    transfer_currency_id: UUID
    min_transfer_amount: float = Field(..., gt=0)
    max_transfer_amount: float = Field(..., gt=0)
    fee_percentage: float = Field(..., ge=0, le=100)
    transfer_method: str
    estimated_transfer_time: Optional[str]  # TODO: update when time field changed
    required_documents: List[DocumentResponse]

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            provider_name=obj.provider.name,
            provider_id=obj.provider.id,
            provider_url=obj.provider.url,  # Added url, don't forget to add a new field here next time too
            send_country_name=obj.send_country.name,
            send_country_id=obj.send_country.id,
            receive_country_name=obj.receive_country.name,
            receive_country_id=obj.receive_country.id,
            transfer_currency_abbreviation=obj.transfer_currency.abbreviation if obj.transfer_currency else None,
            transfer_currency_id=obj.transfer_currency.id if obj.transfer_currency else None,
            min_transfer_amount=obj.min_transfer_amount,
            max_transfer_amount=obj.max_transfer_amount,
            fee_percentage=obj.fee_percentage,
            transfer_method=obj.transfer_method,
            estimated_transfer_time=obj.estimated_transfer_time,
            required_documents=[DocumentResponse(id=doc.id, name=doc.name) for doc in obj.required_documents]
        )


class OptimizedTransferRuleResponse(BaseModel):
    send_country: CountryResponse
    receive_country: CountryResponse
    original_currency: Optional[CurrencyResponse] = None
    rules: List[TransferRuleDetails]
