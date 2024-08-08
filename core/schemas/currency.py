from typing import Optional
from .base import BaseResponse


class CurrencyResponse(BaseResponse):
    name: str
    symbol: str  # TODO: This was Optional I forgot why, doublecheck (!)
    abbreviation: str
