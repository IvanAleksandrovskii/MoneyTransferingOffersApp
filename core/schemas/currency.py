from typing import Optional
from .base import BaseResponse


class CurrencyResponse(BaseResponse):
    name: str
    symbol: Optional[str]
    abbreviation: str
