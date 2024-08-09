from wtforms import validators

from core.admin.models.base import BaseAdminModel
from core.models import TransferProvider


class TransferProviderAdmin(BaseAdminModel, model=TransferProvider):
    column_list = BaseAdminModel.column_list + [TransferProvider.name, TransferProvider.url]
    column_searchable_list = [TransferProvider.name]
    column_sortable_list = BaseAdminModel.column_sortable_list + [TransferProvider.name]
    column_filters = BaseAdminModel.column_filters + [TransferProvider.name]
    form_excluded_columns = ['exchange_rates', 'transfer_rules']
    form_args = {
        'url': {
            'validators': [validators.DataRequired(), validators.URL(), validators.Length(max=255)]
        },
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'url': {
            'placeholder': 'https://example.com'
        },
        'name': {
            'placeholder': 'Enter provider name'
        }
    }
    category = "Providers"
