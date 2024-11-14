__all__ = [
    "DocumentAdmin", "TransferRuleAdmin", "TransferProviderAdmin",
    "CurrencyAdmin", "CountryAdmin", "ProviderExchangeRateAdmin",
    "TgUserAdmin", "TgUserLogAdmin", 
    "ButtonAdmin", "MediaAdmin", "TextAdmin",
    ]

from .exchange_rate import ProviderExchangeRateAdmin
from .transfer_rule import TransferRuleAdmin
from .transfer_provider import TransferProviderAdmin
from .document import DocumentAdmin
from .currency import CurrencyAdmin
from .country import CountryAdmin
from .tg_user import TgUserAdmin, TgUserLogAdmin
from .button import ButtonAdmin
from .media import MediaAdmin
from .text import TextAdmin
