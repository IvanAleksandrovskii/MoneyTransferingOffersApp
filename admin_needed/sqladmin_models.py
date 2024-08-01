from sqladmin import ModelView

from core.models import Country
from core.models import Currency
from core.models import TransferProvider
from core.models import TransferRule


class CountryAdmin(ModelView, model=Country):
    column_list = [Country.id, Country.name, Country.local_currency_id]
    name = "Countrie"  # TODO: wrong written to fix auto naming issue about multiples with "y" on the end
    # category = "" # TODO: group by categories


class CurrencyAdmin(ModelView, model=Currency):
    column_list = [Currency.id, Currency.abbreviation]
    name = "Currencie"  # TODO: wrong written to fix auto naming issue about multiples with "y" on the end
    # category = "" # TODO: group by categories


class TransferProviderAdmin(ModelView, model=TransferProvider):
    column_list = [TransferProvider.id, TransferProvider.name]

    # category = "" # TODO: group by categories


class TransferRuleAdmin(ModelView, model=TransferRule):
    column_list = [TransferRule.id, TransferRule.send_country_id, TransferRule.receive_country_id,
                   TransferRule.transfer_currency_id, TransferRule.provider_id, TransferRule.fee_percentage,
                   TransferRule.min_transfer_amount, TransferRule.max_transfer_amount]

    # category = "" # TODO: group by categories
