from typing import Any

from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import Document


class DocumentAdmin(BaseAdminModel, model=Document):
    column_list = [Document.name] + BaseAdminModel.column_list
    column_searchable_list = [Document.name]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Document.name]
    column_filters = BaseAdminModel.column_filters + [Document.name]
    form_args = {
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'name': {
            'placeholder': 'Enter document name'
        }
    }
    # form_excluded_columns = ['transfer_rules']
    form_columns = ['name', 'is_active']
    name = "Document"
    name_plural = "Documents"
    can_delete = False
    category = "Global"

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        if is_created:
            logger.info(f"Created document: {model.name}")
        else:
            logger.info(f"Updated document: {model.name}")
