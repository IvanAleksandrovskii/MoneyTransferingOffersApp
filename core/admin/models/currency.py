from typing import Any

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request
from wtforms import validators

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
    can_delete = False

    def search_query(self, stmt, term):
        return stmt.filter(
            or_(
                Currency.name.ilike(f"%{term}%"),
                Currency.abbreviation.ilike(f"%{term}%"),
                Currency.symbol.ilike(f"%{term}%")
            )
        )

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            if is_created:
                logger.info(f"Created currency: {model.name} ({model.abbreviation})")
            else:
                logger.info(f"Updated currency: {model.name} ({model.abbreviation})")
        except IntegrityError as e:
            await request.app.state.db.rollback()

            # Unique constraint error
            if "uq_currency_name" in str(e) or "uq_currency_abbreviation" in str(e) or "uq_currency_symbol" in str(e):
                logger.warning(f"Attempt to create duplicate currency: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Currency with this name, abbreviation or symbol already exists"
                )
            else:
                logger.exception(f"Unexpected IntegrityError occurred: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception(f"Unexpected error occurred in after_model_change: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
