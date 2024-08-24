from typing import Any

from starlette.requests import Request
from wtforms import validators

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import Document


class DocumentAdmin(BaseAdminModel, model=Document):
    column_list = [Document.name] + BaseAdminModel.column_list

    column_searchable_list = [Document.name, Document.id]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Document.name]
    column_filters = BaseAdminModel.column_filters + [Document.name, Document.id]

    form_columns = ['name', 'is_active']
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

    name = "Document"
    name_plural = "Documents"
    category = "Global"

    def search_query(self, stmt, term):
        return stmt.filter(Document.name.ilike(f"%{term}%"))

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            action = "Created" if is_created else "Updated"
            logger.info(f"{action} document: {model.name}")
        except Exception as e:
            logger.error(f"Error in after_model_change for document: {e}")
