from .base import BaseResponse


class CurrencyResponse(BaseResponse):
    name: str
    symbol: str
    abbreviation: str
