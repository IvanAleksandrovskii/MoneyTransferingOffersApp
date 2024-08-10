from datetime import datetime

from pydantic import Field, ConfigDict

from .base import BaseResponse
from .provider import ProviderResponse
from .currency import CurrencyResponse


class ExchangeRateResponse(BaseResponse):
    provider: ProviderResponse
    from_currency: CurrencyResponse
    to_currency: CurrencyResponse
    rate: float = Field(..., gt=0)
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

    # @classmethod
    # def model_validate(cls, obj):
    #     return cls(
    #         id=obj.id,
    #         provider=ProviderResponse.model_validate(obj.provider),
    #         from_currency=CurrencyResponse.model_validate(obj.from_currency),
    #         to_currency=CurrencyResponse.model_validate(obj.to_currency),
    #         rate=obj.rate,
    #         last_updated=obj.last_updated
    #     )
