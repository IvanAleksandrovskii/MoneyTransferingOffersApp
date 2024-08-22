from typing import Any
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from wtforms import validators
from fastapi import HTTPException

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import Currency


class CurrencyAdmin(BaseAdminModel, model=Currency):
    column_list = [Currency.abbreviation, Currency.name, Currency.symbol] + BaseAdminModel.column_list

    column_searchable_list = [Currency.name, Currency.abbreviation, Currency.symbol, Currency.id]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Currency.name, Currency.abbreviation, Currency.symbol]
    column_filters = BaseAdminModel.column_filters + [Currency.name, Currency.abbreviation, Currency.symbol, Currency.id]

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

    def search_query(self, stmt, term):
        return stmt.filter(
            or_(
                Currency.name.ilike(f"%{term}%"),
                Currency.abbreviation.ilike(f"%{term}%"),
                Currency.symbol.ilike(f"%{term}%")
            )
        )

    async def delete_model(self, request: Request, pk: Any) -> bool:
        try:
            return await super().delete_model(request, pk)
        except HTTPException as e:
            if e.status_code == 400 and "cannot be deleted" in str(e.detail).lower():
                logger.error("Cannot delete currency: it is set as the local currency for one or more countries")
                raise HTTPException(
                    status_code=400,
                    detail="This currency cannot be deleted because it is set as the local currency for one or more countries."
                )
            raise

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request):
        try:
            if is_created:
                logger.info(f"Created currency: {model.name} ({model.abbreviation})")
            else:
                logger.info(f"Updated currency: {model.name} ({model.abbreviation})")
        except IntegrityError as e:
            await request.app.state.db.rollback()
            logger.warning(f"Integrity error when creating/updating currency: {e}")
            raise HTTPException(status_code=400, detail="A currency with this name, abbreviation or symbol already exists.")
        except Exception as e:
            logger.exception(f"Unexpected error occurred in after_model_change: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing your request.")
