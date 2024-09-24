__all__ = ["DocumentAdmin", "TransferRuleAdmin", "TransferProviderAdmin",
           "CurrencyAdmin", "CountryAdmin", "ProviderExchangeRateAdmin",
           "TgUserAdmin", "TgUserLogAdmin", "WelcomeMessageAdmin"]

from .exchange_rate import ProviderExchangeRateAdmin
from .transfer_rule import TransferRuleAdmin
from .transfer_provider import TransferProviderAdmin
from .document import DocumentAdmin
from .currency import CurrencyAdmin
from .country import CountryAdmin
from .tg_user import TgUserAdmin, TgUserLogAdmin
from .tg_welcome_message import WelcomeMessageAdmin
