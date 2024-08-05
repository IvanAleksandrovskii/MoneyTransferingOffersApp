from sqladmin import ModelView

from core.models import Country
from core.models import Currency
from core.models import TransferProvider
from core.models import TransferRule
from core.models import ProviderExchangeRate


class CountryAdmin(ModelView, model=Country):
    column_list = [Country.id, Country.name, Country.is_active, Country.local_currency_id]
    name = "Country"
    # category = "" # TODO: group by categories


class CurrencyAdmin(ModelView, model=Currency):
    column_list = [Currency.id, Currency.abbreviation, Currency.is_active, Currency.name, Currency.symbol]
    name = "Currency"
    # category = "" # TODO: group by categories


class TransferProviderAdmin(ModelView, model=TransferProvider):
    column_list = [TransferProvider.id, TransferProvider.name, TransferProvider.is_active]
    # category = "" # TODO: group by categories


class TransferRuleAdmin(ModelView, model=TransferRule):
    column_list = [TransferRule.id, TransferRule.is_active, TransferRule.send_country_id,
                   TransferRule.receive_country_id, TransferRule.transfer_currency_id, TransferRule.provider_id,
                   TransferRule.fee_percentage, TransferRule.min_transfer_amount, TransferRule.max_transfer_amount]
    # category = "" # TODO: group by categories


class ProviderExchangeRateAdmin(ModelView, model=ProviderExchangeRate):
    column_list = [ProviderExchangeRate.id, ProviderExchangeRate.is_active, ProviderExchangeRate.provider_id,
                   ProviderExchangeRate.from_currency_id, ProviderExchangeRate.to_currency_id,
                   ProviderExchangeRate.rate, ProviderExchangeRate.last_updated]
    name = "Provider Exchange Rate"
    # category = "" # TODO: group by categories
