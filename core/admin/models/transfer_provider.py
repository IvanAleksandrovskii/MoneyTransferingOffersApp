from wtforms import validators

from core.admin.models.base import BaseAdminModel
from core.models import TransferProvider


class TransferProviderAdmin(BaseAdminModel, model=TransferProvider):
    column_list = [TransferProvider.name, TransferProvider.url] + BaseAdminModel.column_list
    column_searchable_list = [TransferProvider.name]
    column_sortable_list = BaseAdminModel.column_sortable_list + [TransferProvider.name]
    column_filters = BaseAdminModel.column_filters + [TransferProvider.name]
    # form_excluded_columns = ['exchange_rates', 'transfer_rules']
    form_columns = ['name', 'url', 'is_active']
    form_args = {
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        },
        'url': {
            'validators': [validators.DataRequired(), validators.URL(), validators.Length(max=255)]
        }
    }
    form_widget_args = {
        'name': {
            'placeholder': 'Enter provider name'
        },
        'url': {
            'placeholder': 'https://example.com'
        },
    }
    category = "Providers"
