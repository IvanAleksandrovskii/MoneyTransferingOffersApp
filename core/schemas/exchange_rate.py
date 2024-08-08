from datetime import datetime

from pydantic import Field

from .base import BaseResponse
from .provider import ProviderResponse
from .currency import CurrencyResponse


class ExchangeRateResponse(BaseResponse):
    provider: ProviderResponse
    from_currency: CurrencyResponse
    to_currency: CurrencyResponse
    rate: float = Field(..., gt=0)
    last_updated: datetime
