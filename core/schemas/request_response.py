from uuid import UUID

from pydantic import BaseModel, UUID4, ConfigDict
from typing import List, Optional, Union
from datetime import datetime


class CurrencyResponse(BaseModel):
    id: UUID4
    name: str
    symbol: Optional[str]
    abbreviation: str

    model_config = ConfigDict(from_attributes=True)


class CountryResponse(BaseModel):
    id: UUID4
    name: str
    local_currency: CurrencyResponse

    model_config = ConfigDict(from_attributes=True)


class ProviderResponse(BaseModel):
    id: UUID4
    name: str

    model_config = ConfigDict(from_attributes=True)


class TransferRuleResponse(BaseModel):
    id: UUID4
    send_country: CountryResponse
    receive_country: CountryResponse
    provider: ProviderResponse
    transfer_method: str
    estimated_transfer_time: Optional[str]
    required_documents: Optional[str]

    # TODO: New fields added (!), still need to improve
    original_amount: float
    original_currency: CurrencyResponse
    converted_amount: float
    transfer_currency: CurrencyResponse
    amount_received: float
    transfer_fee: float
    transfer_fee_percentage: float
    min_transfer_amount: float
    max_transfer_amount: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class ExchangeRateResponse(BaseModel):
    id: UUID4
    provider: ProviderResponse
    from_currency: CurrencyResponse
    to_currency: CurrencyResponse
    rate: float
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class TransferRuleRequest(BaseModel):
    send_country: Union[str, UUID]
    receive_country: Union[str, UUID]


class TransferRuleFullRequest(BaseModel):
    send_country: Union[str, UUID]
    receive_country: Union[str, UUID]
    from_currency: Union[str, UUID]
    amount: float


class TransferRuleDetails(BaseModel):
    id: UUID4
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


class OptimizedTransferRuleResponse(BaseModel):
    send_country: CountryResponse
    receive_country: CountryResponse
    original_currency: CurrencyResponse
    rules: List[TransferRuleDetails]
