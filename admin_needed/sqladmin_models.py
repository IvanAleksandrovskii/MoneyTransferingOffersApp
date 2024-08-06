from sqladmin import ModelView

from core import logger
from core.models import Country
from core.models import Currency
from core.models import TransferProvider
from core.models import TransferRule
from core.models import ProviderExchangeRate


def format_exchange_rate(model, name):
    return f"{model.provider.name} - {model.from_currency.abbreviation} - {model.to_currency.abbreviation}"


def format_transfer_rule(model, name):
    return f"{model.provider.name} - {model.send_country.name} - {model.receive_country.name} - {model.transfer_currency.abbreviation if model.transfer_currency else 'Unknown'} - {model.min_transfer_amount} - {model.max_transfer_amount}"


class CountryAdmin(ModelView, model=Country):
    column_list = [Country.id, Country.name, Country.is_active, Country.local_currency_id]
    name = "Country"
    name_plural = "Countries"
    # category = "" # TODO: group by categories


class CurrencyAdmin(ModelView, model=Currency):
    column_list = [Currency.id, Currency.abbreviation, Currency.is_active, Currency.name, Currency.symbol]
    name = "Currency"
    name_plural = "Currencies"
    # category = "" # TODO: group by categories


class TransferProviderAdmin(ModelView, model=TransferProvider):
    column_list = [TransferProvider.id, TransferProvider.name, TransferProvider.is_active]
    form_excluded_columns = ['exchange_rates', 'transfer_rules']
    # category = "" # TODO: group by categories


class TransferRuleAdmin(ModelView, model=TransferRule):
    column_list = [
        "formatted_transfer_rule",
        TransferRule.id,
        TransferRule.is_active,
        TransferRule.send_country_id,
        TransferRule.receive_country_id,
        TransferRule.transfer_currency_id,
        TransferRule.provider_id,
        TransferRule.fee_percentage,
        TransferRule.min_transfer_amount,
        TransferRule.max_transfer_amount
    ]
    column_formatters = {
        "formatted_transfer_rule": format_transfer_rule
    }
    name = "Transfer Rule"
    # category = "" # TODO: group by categories


class ProviderExchangeRateAdmin(ModelView, model=ProviderExchangeRate):
    column_list = [
        "formatted_exchange_rate",
        ProviderExchangeRate.id,
        ProviderExchangeRate.is_active,
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id,
        ProviderExchangeRate.rate,
        ProviderExchangeRate.last_updated
    ]
    column_formatters = {
        "formatted_exchange_rate": format_exchange_rate
    }
    name = "Provider Exchange Rate"
    # category = "" # TODO: group by categories
