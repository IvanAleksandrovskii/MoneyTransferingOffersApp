from .base import BaseResponse
from .currency import CurrencyResponse


class CountryResponse(BaseResponse):
    name: str
    abbreviation: str
    local_currency: CurrencyResponse

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            name=obj.name,
            abbreviation=obj.abbreviation,
            local_currency=CurrencyResponse.model_validate(obj.local_currency)
        )
