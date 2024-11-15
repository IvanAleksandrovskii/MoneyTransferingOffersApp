from typing import Any

from sqlalchemy import or_
from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.admin.services.formatting_for_models import format_exchange_rate
from core.models import ProviderExchangeRate, TransferProvider, Currency


class ProviderExchangeRateAdmin(BaseAdminModel, model=ProviderExchangeRate):
    column_list = ["formatted_exchange_rate", ProviderExchangeRate.rate] + BaseAdminModel.column_list + [
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

    form_columns = ["provider", "from_currency", "to_currency", "rate", "is_active"]

    column_searchable_list = [
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id,
        'provider.name',
        'from_currency.name',
        'to_currency.name',
        'from_currency.abbreviation',
        'to_currency.abbreviation',
    ]
    column_sortable_list = BaseAdminModel.column_sortable_list + [
        ProviderExchangeRate.rate,
        ProviderExchangeRate.last_updated,
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id
    ]
    column_filters = BaseAdminModel.column_filters + [
        ProviderExchangeRate.rate,
        ProviderExchangeRate.last_updated,
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id,
        ProviderExchangeRate.id
    ]

    form_args = {
        'rate': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0)]
        },
        'provider': {
            'validators': [validators.DataRequired()]
        },
        'from_currency': {
            'validators': [validators.DataRequired()]
        },
        'to_currency': {
            'validators': [validators.DataRequired()]
        }
    }

    name = "Provider Exchange Rate"
    category = "Providers"
    icon = "fa-solid fa-chart-line"

    def search_query(self, stmt, term):
        return stmt.filter(
            or_(
                ProviderExchangeRate.provider.has(TransferProvider.name.ilike(f"%{term}%")),
                ProviderExchangeRate.from_currency.has(Currency.name.ilike(f"%{term}%")),
                ProviderExchangeRate.to_currency.has(Currency.name.ilike(f"%{term}%")),
                ProviderExchangeRate.from_currency.has(Currency.abbreviation.ilike(f"%{term}%")),
                ProviderExchangeRate.to_currency.has(Currency.abbreviation.ilike(f"%{term}%"))
            )
        )

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            action = "Created" if is_created else "Updated"
            logger.info(f"{action} exchange rate successfully")
        except Exception as e:
            logger.error(f"Error in after_model_change for exchange rate: {e}")
