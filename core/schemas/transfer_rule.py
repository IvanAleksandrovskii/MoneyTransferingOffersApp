from typing import Optional, List
from uuid import UUID

from .base import BaseResponse
from .currency import CurrencyResponse
from .provider import ProviderResponse


class TransferRuleDetails(BaseResponse):
    provider: ProviderResponse
    transfer_method: str
    estimated_transfer_time: Optional[str]
    required_documents: Optional[str]
    original_amount: float
    converted_amount: float
    transfer_currency: CurrencyResponse
    amount_received: float
    transfer_fee: float
    transfer_fee_percentage: float
    min_transfer_amount: float
    max_transfer_amount: Optional[float]
    exchange_rate: float
    conversion_path: List[str]


class DetailedTransferRuleResponse(BaseResponse):
    provider_name: str
    provider_id: UUID
    send_country_name: str
    send_country_id: UUID
    receive_country_name: str
    receive_country_id: UUID
    transfer_currency_abbreviation: str
    transfer_currency_id: UUID
    min_transfer_amount: float
    max_transfer_amount: Optional[float]
    fee_percentage: float
    transfer_method: str
    estimated_transfer_time: Optional[str]
    required_documents: Optional[str]

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            provider_name=obj.provider.name,
            provider_id=obj.provider.id,
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
