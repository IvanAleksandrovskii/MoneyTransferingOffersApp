from typing import Any

from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import Country


class CountryAdmin(BaseAdminModel, model=Country):
    column_list = BaseAdminModel.column_list + [Country.name, Country.local_currency_id]
    column_searchable_list = [Country.name]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Country.name]
    column_filters = BaseAdminModel.column_filters + [Country.name, Country.local_currency_id]
    form_columns = ['name', 'local_currency', 'is_active']
    form_args = {
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'name': {
            'placeholder': 'Enter country name'
        }
    }
    name = "Country"
    name_plural = "Countries"
    category = "Global"
    can_delete = False

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        logger.info(f"{'Created' if is_created else 'Updated'} country: {model.name}")
