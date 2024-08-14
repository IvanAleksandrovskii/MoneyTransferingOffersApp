from typing import Any

from sqlalchemy import or_
from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import TransferProvider


class TransferProviderAdmin(BaseAdminModel, model=TransferProvider):
    column_list = [TransferProvider.name, TransferProvider.url] + BaseAdminModel.column_list

    column_searchable_list = [TransferProvider.name, TransferProvider.url, TransferProvider.id]
    column_sortable_list = BaseAdminModel.column_sortable_list + [TransferProvider.name, TransferProvider.url]
    column_filters = BaseAdminModel.column_filters + [TransferProvider.name, TransferProvider.url, TransferProvider.id]

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

    def search_query(self, stmt, term):
        return stmt.filter(
            or_(
                TransferProvider.name.ilike(f"%{term}%"),
                TransferProvider.url.ilike(f"%{term}%")
            )
        )

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        if is_created:
            logger.info(f"Created transfer provider: {model.name}")
        else:
            logger.info(f"Updated transfer provider: {model.name}")
