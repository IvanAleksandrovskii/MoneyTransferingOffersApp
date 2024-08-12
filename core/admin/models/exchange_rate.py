from wtforms import validators

from core.admin.models.base import BaseAdminModel
from core.admin.services.formatting_for_models import format_exchange_rate
from core.models import ProviderExchangeRate


class ProviderExchangeRateAdmin(BaseAdminModel, model=ProviderExchangeRate):
    column_list = ["formatted_exchange_rate", ProviderExchangeRate.rate, ] + BaseAdminModel.column_list + [
        ProviderExchangeRate.last_updated,
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id
    ]
    column_formatters = {
        "last_updated": lambda m, a: m.last_updated.strftime("%Y-%m-%d %H:%M:%S") if m.last_updated else "",
        "formatted_exchange_rate": format_exchange_rate,
        "provider": lambda m, a: str(m.provider),
        "from_currency": lambda m, a: str(m.from_currency),
        "to_currency": lambda m, a: str(m.to_currency),
    }
    column_sortable_list = BaseAdminModel.column_sortable_list + [ProviderExchangeRate.rate,
                                                                  ProviderExchangeRate.last_updated]
    column_filters = BaseAdminModel.column_filters + [
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id
    ]
    # form_excluded_columns = ["last_updated"]
    form_columns = ["provider", "from_currency", "to_currency", "rate", "is_active"]
    form_args = {
        'rate': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0)]
        }
    }
    name = "Provider Exchange Rate"
    category = "Providers"
