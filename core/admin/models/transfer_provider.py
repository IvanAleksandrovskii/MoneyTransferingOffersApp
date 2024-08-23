from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from wtforms import validators
from fastapi import UploadFile

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import TransferProvider, db_helper
from core import storage


class TransferProviderAdmin(BaseAdminModel, model=TransferProvider):
    column_list = [TransferProvider.name, TransferProvider.url, TransferProvider.logo] + BaseAdminModel.column_list

    column_searchable_list = [TransferProvider.name, TransferProvider.url, TransferProvider.id]
    column_sortable_list = BaseAdminModel.column_sortable_list + [TransferProvider.name, TransferProvider.url]
    column_filters = BaseAdminModel.column_filters + [TransferProvider.name, TransferProvider.url, TransferProvider.id]

    form_columns = ['name', 'url', 'is_active', 'logo']
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
        logger.debug(f"Searching for term: {term}")
        return stmt.filter(
            or_(
                TransferProvider.name.ilike(f"%{term}%"),
                TransferProvider.url.ilike(f"%{term}%")
            )
        )

    async def get_object(self, pk: Any) -> TransferProvider | None:
        async with AsyncSession(db_helper.engine) as session:
            try:
                stmt = select(TransferProvider).where(TransferProvider.id == pk)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error(f"Error getting TransferProvider with pk {pk}: {str(e)}")
                return None

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        action = "Created" if is_created else "Updated"
        logger.info(f"{action} transfer provider: {model.name}")

        # Process logo upload
        logo = data.get('logo')
        if logo and isinstance(logo, UploadFile):
            try:
                contents = await logo.read()
                file_path = await storage.save(logo.filename, contents)
                model.logo = file_path
                logger.info(f"Logo uploaded for provider: {model.name}")
            except Exception as e:
                logger.error(f"Error uploading logo for provider {model.name}: {str(e)}")

    # TODO: Deleting not working, need to WRITE a storage delete function (!)
    # async def delete_model(self, request: Request, pk: Any):
    #     model = await self.get_object(pk)
    #     if model and model.logo:
    #         try:
    #             await storage.delete(model.logo.name)
    #             logger.info(f"Logo deleted for provider: {model.name}")
    #         except Exception as e:
    #             logger.error(f"Error deleting logo for provider {model.name}: {str(e)}")
    #     return await super().delete_model(request, pk)

