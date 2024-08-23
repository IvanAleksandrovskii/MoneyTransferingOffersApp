from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import Country, Currency


class CountryAdmin(BaseAdminModel, model=Country):
    column_list = [Country.name, Country.abbreviation] + BaseAdminModel.column_list + [Country.local_currency_id]

    column_searchable_list = [Country.name, Country.abbreviation, Country.id]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Country.name, Country.abbreviation]
    column_filters = BaseAdminModel.column_filters + [Country.name, Country.abbreviation, Country.id, Country.local_currency_id]

    form_columns = ['name', 'abbreviation', 'local_currency', 'is_active']
    column_formatters = {
        'local_currency': lambda m, a: str(m.local_currency)
    }
    form_args = {
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        },
        'abbreviation': {
            'validators': [validators.DataRequired(), validators.Length(min=3, max=3)]
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

    def get_query(self):
        return super().get_query().options(joinedload(Country.local_currency))

    def search_query(self, stmt, term):
        return stmt.outerjoin(Currency, Country.local_currency).filter(
            or_(
                Country.name.ilike(f"%{term}%"),
                Country.abbreviation.ilike(f"%{term}%"),
                Currency.name.ilike(f"%{term}%"),
                Currency.abbreviation.ilike(f"%{term}%")
            )
        )

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        if is_created:
            logger.info(f"Created country: {model.name}, abbreviation: {model.abbreviation}")
        else:
            logger.info(f"Updated country: {model.name}, abbreviation: {model.abbreviation}")
