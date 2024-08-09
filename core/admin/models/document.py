from wtforms import validators

from core.admin.models.base import BaseAdminModel
from core.models import Document


class DocumentAdmin(BaseAdminModel, model=Document):
    column_list = BaseAdminModel.column_list + [Document.name]
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
    form_excluded_columns = ['transfer_rules']
    name = "Document"
    name_plural = "Documents"
    can_delete = False
    category = "Global"
