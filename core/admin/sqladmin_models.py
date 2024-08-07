from sqladmin import ModelView

from core.models import Country
from core.models import Currency
from core.models import TransferProvider
from core.models import TransferRule
from core.models import ProviderExchangeRate


def format_exchange_rate(model, name):  # Do not delete name form here in is not unused (!), needed for formatting
    return f"{model.provider.name} - {model.from_currency.abbreviation} - {model.to_currency.abbreviation}"


def format_transfer_rule(model, name):  # Do not delete name form here in is not unused (!), needed for formatting
    return (f"{model.provider.name} - {model.send_country.name} - {model.receive_country.name} - "
            f"{model.transfer_currency.abbreviation if model.transfer_currency else 'Unknown'} - "
            f"{model.min_transfer_amount} - {model.max_transfer_amount}")


class CountryAdmin(ModelView, model=Country):
    column_list = [Country.name, Country.id, Country.is_active, Country.local_currency_id]
    name = "Country"
    name_plural = "Countries"
    category = "Global"  # Done todo double check


class CurrencyAdmin(ModelView, model=Currency):
    column_list = [Currency.abbreviation, Currency.id, Currency.is_active, Currency.name, Currency.symbol]
    name = "Currency"
    name_plural = "Currencies"
    category = "Global"  # Done todo double check


class TransferProviderAdmin(ModelView, model=TransferProvider):
    column_list = [TransferProvider.name, TransferProvider.id, TransferProvider.is_active, TransferProvider.url]
    form_excluded_columns = ['exchange_rates', 'transfer_rules']
    category = "Providers"  # Done todo double check


class TransferRuleAdmin(ModelView, model=TransferRule):
    column_list = [
        "formatted_transfer_rule",
        TransferRule.id,
        TransferRule.is_active,
        TransferRule.fee_percentage,
        TransferRule.min_transfer_amount,
        TransferRule.max_transfer_amount,
        TransferRule.send_country_id,
        TransferRule.receive_country_id,
        TransferRule.transfer_currency_id,
        TransferRule.provider_id
    ]
    column_formatters = {
        "formatted_transfer_rule": format_transfer_rule
    }
    name = "Transfer Rule"
    category = "Providers"  # Done todo double check


class ProviderExchangeRateAdmin(ModelView, model=ProviderExchangeRate):
    column_list = [
        "formatted_exchange_rate",
        ProviderExchangeRate.rate,
        ProviderExchangeRate.id,
        ProviderExchangeRate.last_updated,
        ProviderExchangeRate.is_active,
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id
    ]
    form_excluded_columns = [
        "last_updated"
    ]
    column_formatters = {
        "last_updated": lambda m, a: m.last_updated.strftime("%Y-%m-%d %H:%M:%S") if m.last_updated else "",
        "formatted_exchange_rate": format_exchange_rate
    }
    name = "Provider Exchange Rate"
    category = "Providers"  # Done todo double check
