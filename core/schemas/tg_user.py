from pydantic import BaseModel


class TgUserCreate(BaseModel):
    tg_user: str


class TgUserLogCreate(BaseModel):
    tg_user: str
    url_log: str
    amount_log: str
    currency_log: str
