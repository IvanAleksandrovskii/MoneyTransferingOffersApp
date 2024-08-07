from typing import List
from uuid import UUID

from .base import BaseResponse
from .currency import CurrencyResponse


class CountryResponse(BaseResponse):
    name: str
    local_currency: CurrencyResponse

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            name=obj.name,
            local_currency=CurrencyResponse.model_validate(obj.local_currency)
        )
