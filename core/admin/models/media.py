# core/admin/models/media.py
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from fastapi import UploadFile

from .base import BaseAdminModel
from core.models import Media
from core import logger
from core.models import db_helper
from core.fastapi_storage import bot_storage


class MediaAdmin(BaseAdminModel, model=Media):
    column_list = [Media.id, Media.file, Media.file_type, Media.description, Media.is_active]  # , Media.created_at, Media.updated_at
    column_details_list = [Media.id, Media.file, Media.file_type, Media.description, Media.is_active, Media.texts]  # , Media.created_at, Media.updated_at
    column_sortable_list = [Media.id, Media.file_type, Media.is_active]  # , Media.created_at, Media.updated_at
    column_searchable_list = [Media.id, Media.file_type, Media.description]
    column_filters = [Media.file_type, Media.is_active]

    form_columns = [Media.file, Media.file_type, Media.description, Media.is_active]

    name = "Media"
    name_plural = "Media Files"
    icon = "fa-solid fa-image"

    category = "Important Data"
    
    async def get_object(self, pk: Any) -> Media | None:
        async with AsyncSession(db_helper.engine) as session:
            try:
                stmt = select(Media).where(Media.id == pk)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error(f"Error getting Media with pk {pk}: {str(e)}")
                return None
    
    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            action = "Created" if is_created else "Updated"
            logger.info(f"{action} Media")
        except Exception as e:
            logger.error(f"Error in after_model_change for Media: {e}")

        # Process file upload
        file = data.get('file')
        if file and isinstance(file, UploadFile):
            try:
                contents = await file.read()
                file_path = await bot_storage.save(file.filename, contents)
                model.file = file_path
                logger.info(f"File uploaded")
            except Exception as e:
                logger.error(f"Error uploading file: {str(e)}")

    async def delete_model(self, request: Request, pk: Any):
        model = await self.get_object(pk)
        if model and model.file:
            try:
                bot_storage.delete(model.file)
                logger.info(f"File deleted")
            except Exception as e:
                logger.error(f"Error deleting file: {str(e)}")
        return await super().delete_model(request, pk)

