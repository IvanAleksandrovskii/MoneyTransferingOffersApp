from typing import Union
from uuid import UUID
from pydantic import BaseModel


class TransferRuleRequest(BaseModel):
    send_country: Union[str, UUID]
    receive_country: Union[str, UUID]


class TransferRuleRequestByName(BaseModel):
    send_country: str
    receive_country: str


class TransferRuleFullRequest(BaseModel):
    send_country: Union[str, UUID]
    receive_country: Union[str, UUID]
    from_currency: Union[str, UUID]
    amount: float
