from typing import Optional, List
from uuid import UUID
from datetime import timedelta

from pydantic import BaseModel, Field, model_validator

from . import DocumentResponse
from .base import BaseResponse
from .country import CountryResponse
from .currency import CurrencyResponse
from .provider import ProviderResponse
from .time_delta_info import TimeDeltaInfo


class TransferRuleDetails(BaseModel):
    id: UUID
    provider: ProviderResponse
    transfer_method: str
    # estimated_transfer_time: Optional[str] = None  # TODO: update when time field changed
    min_transfer_time: TimeDeltaInfo
    max_transfer_time: TimeDeltaInfo
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
    def validate_transfer_times(self) -> 'TransferRuleDetails':
        min_time = self.min_transfer_time.to_timedelta()
        max_time = self.max_transfer_time.to_timedelta()

        if min_time < timedelta(0):
            raise ValueError('min_transfer_time must be non-negative')

        if max_time < timedelta(0):
            raise ValueError('max_transfer_time must be non-negative')

        if max_time < min_time:
            raise ValueError('max_transfer_time must be greater than or equal to min_transfer_time')

        return self

    model_config = {
        "extra": "forbid",  # This will raise an error if extra fields are provided
    }


class DetailedTransferRuleResponse(BaseResponse):
    provider_name: str
    provider_id: UUID
    provider_url: str | None
    send_country: CountryResponse
    receive_country: CountryResponse
    transfer_currency: CurrencyResponse
    min_transfer_amount: float = Field(..., gt=0)
    max_transfer_amount: float = Field(..., gt=0)
    fee_percentage: float = Field(..., ge=0, le=100)
    transfer_method: str
    min_transfer_time: TimeDeltaInfo
    max_transfer_time: TimeDeltaInfo
    required_documents: List[DocumentResponse]

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            provider_name=obj.provider.name,
            provider_id=obj.provider.id,
            provider_url=obj.provider.url,
            send_country=CountryResponse.model_validate(obj.send_country),
            receive_country=CountryResponse.model_validate(obj.receive_country),
            transfer_currency=CurrencyResponse.model_validate(obj.transfer_currency),
            min_transfer_amount=obj.min_transfer_amount,
            max_transfer_amount=obj.max_transfer_amount,
            fee_percentage=obj.fee_percentage,
            transfer_method=obj.transfer_method,
            min_transfer_time=TimeDeltaInfo(
                days=obj.min_transfer_time.days,
                hours=obj.min_transfer_time.seconds // 3600,
                minutes=(obj.min_transfer_time.seconds % 3600) // 60
            ),
            max_transfer_time=TimeDeltaInfo(
                days=obj.max_transfer_time.days,
                hours=obj.max_transfer_time.seconds // 3600,
                minutes=(obj.max_transfer_time.seconds % 3600) // 60
            ),
            required_documents=[DocumentResponse(id=doc.id, name=doc.name) for doc in obj.required_documents]
        )


class OptimizedTransferRuleResponse(BaseModel):
    send_country: CountryResponse
    receive_country: CountryResponse
    original_currency: Optional[CurrencyResponse] = None
    rules: List[TransferRuleDetails]


class DetailedTransferRuleResponseNoProviderVersion(BaseResponse):
    send_country: CountryResponse
    receive_country: CountryResponse
    transfer_currency: CurrencyResponse
    min_transfer_amount: float = Field(..., gt=0)
    max_transfer_amount: float = Field(..., gt=0)
    fee_percentage: float = Field(..., ge=0, le=100)
    transfer_method: str
    min_transfer_time: TimeDeltaInfo
    max_transfer_time: TimeDeltaInfo
    required_documents: List[DocumentResponse]

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            send_country=CountryResponse.model_validate(obj.send_country),
            receive_country=CountryResponse.model_validate(obj.receive_country),
            transfer_currency=CurrencyResponse.model_validate(obj.transfer_currency),
            min_transfer_amount=obj.min_transfer_amount,
            max_transfer_amount=obj.max_transfer_amount,
            fee_percentage=obj.fee_percentage,
            transfer_method=obj.transfer_method,
            min_transfer_time=TimeDeltaInfo(
                days=obj.min_transfer_time.days,
                hours=obj.min_transfer_time.seconds // 3600,
                minutes=(obj.min_transfer_time.seconds % 3600) // 60
            ),
            max_transfer_time=TimeDeltaInfo(
                days=obj.max_transfer_time.days,
                hours=obj.max_transfer_time.seconds // 3600,
                minutes=(obj.max_transfer_time.seconds % 3600) // 60
            ),
            required_documents=[DocumentResponse(id=doc.id, name=doc.name) for doc in obj.required_documents]
        )
