from datetime import datetime
from .base import BaseResponse
from .provider import ProviderResponse
from .currency import CurrencyResponse


class ExchangeRateResponse(BaseResponse):
    provider: ProviderResponse
    from_currency: CurrencyResponse
    to_currency: CurrencyResponse
    rate: float
    last_updated: datetime
