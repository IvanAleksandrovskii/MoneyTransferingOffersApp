from typing import Optional

from pydantic import BaseModel, Field


class TgUserCreate(BaseModel):
    tg_user: str


class TgUserLogCreate(BaseModel):
    tg_user: str
    url_log: str
    amount_log: Optional[str] = Field(default=None)
    currency_log: Optional[str] = Field(default=None)
    send_country_log: Optional[str] = Field(default=None)
    receive_country_log: Optional[str] = Field(default=None)
