from typing import List
from pydantic import BaseModel
from .country import CountryResponse
from .currency import CurrencyResponse
from .transfer_rule import TransferRuleDetails


class OptimizedTransferRuleResponse(BaseModel):
    send_country: CountryResponse
    receive_country: CountryResponse
    original_currency: CurrencyResponse
    rules: List[TransferRuleDetails]
