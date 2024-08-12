from wtforms import validators

from core.admin.models.base import BaseAdminModel
from core.models import Currency


class CurrencyAdmin(BaseAdminModel, model=Currency):
    column_list = [Currency.abbreviation, Currency.name, Currency.symbol] + BaseAdminModel.column_list
    column_searchable_list = [Currency.name, Currency.abbreviation]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Currency.name, Currency.abbreviation]
    column_filters = BaseAdminModel.column_filters + [Currency.name, Currency.abbreviation]
    # form_excluded_columns = ['countries']
    form_columns = ['name', 'abbreviation', 'symbol', 'is_active']
    form_args = {
        'abbreviation': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=3)]
        },
        'symbol': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=5)]
        },
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'abbreviation': {
            'placeholder': 'e.g. USD'
        },
        'symbol': {
            'placeholder': 'e.g. $'
        },
        'name': {
            'placeholder': 'e.g. US Dollar'
        }
    }
    name = "Currency"
    name_plural = "Currencies"
    category = "Global"
    can_delete = False
