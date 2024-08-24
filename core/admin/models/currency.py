from typing import Any
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from wtforms import validators
from fastapi import HTTPException
from starlette.responses import RedirectResponse

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
            'validators': [validators.DataRequired(), validators.Length(min=3, max=3)]
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

    async def delete_model(self, request: Request, pk: Any) -> Any:
        try:
            result = await super().delete_model(request, pk)
            if result is None:
                logger.warning(f"Delete operation for currency with pk {pk} returned None")
                return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)
            return result
        except IntegrityError as e:
            error_message = str(e)
            logger.error(f"IntegrityError in delete_model for currency: {error_message}")
            if "foreign key constraint" in error_message.lower():
                error = "This currency cannot be deleted because it is associated with one or more countries. Please remove the currency from all countries before deleting it."
            else:
                error = "An error occurred while deleting the currency. It may be referenced by other records."
        except Exception as e:
            logger.error(f"Unexpected error in delete_model for currency: {str(e)}")
            error = "An unexpected error occurred while deleting the currency."

        # Create URL and add error param
        url = request.url_for("admin:list", identity=self.identity)
        url = url.include_query_params(error=error)

        return RedirectResponse(url, status_code=302)

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request):
        try:
            action = "Created" if is_created else "Updated"
            logger.info(f"{action} currency: {model.name} ({model.abbreviation})")
        except Exception as e:
            logger.exception(f"Unexpected error occurred in after_model_change: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing your request.")
