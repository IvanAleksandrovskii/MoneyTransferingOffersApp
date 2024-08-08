from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseResponse
from .country import CountryResponse
from .currency import CurrencyResponse
from .provider import ProviderResponse


class TransferRuleDetails(BaseResponse):
    provider: ProviderResponse
    transfer_method: str
    estimated_transfer_time: Optional[str]  # TODO: update when time field changed
    required_documents: Optional[str]  # TODO: update to List[obj] when document obj is created
    original_amount: float = Field(..., gt=0)
    converted_amount: float = Field(..., gt=0)
    transfer_currency: CurrencyResponse
    amount_received: float = Field(..., ge=0)
    transfer_fee: float = Field(..., ge=0)
    transfer_fee_percentage: float = Field(..., ge=0, le=100)
    min_transfer_amount: float = Field(..., gt=0)
    max_transfer_amount: float = Field(..., gt=0)
    exchange_rate: float = Field(..., gt=0)
    conversion_path: List[str | None]


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
    required_documents: Optional[str]  # TODO: update when document obj is created

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
            required_documents=obj.required_documents
        )


class OptimizedTransferRuleResponse(BaseModel):
    send_country: CountryResponse
    receive_country: CountryResponse
    original_currency: CurrencyResponse
    rules: List[TransferRuleDetails]
