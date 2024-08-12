from typing import Any

from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import Country


class CountryAdmin(BaseAdminModel, model=Country):
    # This is an all-country part
    column_list = [Country.name, ] + BaseAdminModel.column_list + [Country.local_currency_id, ]
    column_searchable_list = [Country.name, Country.abbreviation]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Country.name, Country.abbreviation]
    column_filters = BaseAdminModel.column_filters + [Country.name, Country.abbreviation, Country.local_currency_id]
    form_columns = ['name', 'abbreviation', 'local_currency', 'is_active']
    column_formatters = {
        'local_currency': lambda m, a: str(m.local_currency)
    }
    form_args = {
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'name': {
            'placeholder': 'Enter country name'
        },
        'abbreviation': {
            'placeholder': 'Enter country abbreviation'
        }
    }
    name = "Country"
    name_plural = "Countries"
    category = "Global"
    can_delete = False

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        if is_created:
            logger.info(f"Created country: {model.name}, abbreviation: {model.abbreviation}")
        else:
            logger.info(f"Updated country: {model.name}, abbreviation: {model.abbreviation}")
