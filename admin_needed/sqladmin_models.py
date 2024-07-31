from sqladmin import ModelView

from core.models import Country
from core.models import Currency
from core.models import TransferProvider
from core.models import TransferRule


class CountryAdmin(ModelView, model=Country):
    column_list = [Country.id, Country.name, Country.local_currency_id]
    name = "Countries"
    # category = ""


class CurrencyAdmin(ModelView, model=Currency):
    column_list = [Currency.id, Currency.abbreviation]
    name = "Currencies"
    # category = ""


class TransferProviderAdmin(ModelView, model=TransferProvider):
    column_list = [TransferProvider.id, TransferProvider.name]
    name = "Transfer Providers"
    # category = ""


class TransferRuleAdmin(ModelView, model=TransferRule):
    column_list = [TransferRule.id, TransferRule.send_country_id, TransferRule.receive_country_id,
                   TransferRule.currency_id, TransferRule.provider_id, TransferRule.fee_percentage,
                   TransferRule.min_transfer_amount, TransferRule.max_transfer_amount]
    name = "Transfer Rules"
    # category = ""
