from typing import List

from pydantic import BaseModel

from .transfer_rule import DetailedTransferRuleResponseNoProviderVersion
from .provider import ProviderResponse


class ProviderTransferRulesResponse(BaseModel):
    provider: ProviderResponse
    transfer_rules: List[DetailedTransferRuleResponseNoProviderVersion]
