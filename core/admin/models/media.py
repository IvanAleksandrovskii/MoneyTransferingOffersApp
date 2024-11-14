# core/admin/models/media.py

from fastapi import UploadFile

from .base import BaseAdminModel
from core.models import Media
from core import logger as log
from core.fastapi_storage import bot_storage


class MediaAdmin(BaseAdminModel, model=Media):
    column_list = [Media.id, Media.file, Media.file_type, Media.description, Media.is_active, Media.created_at, Media.updated_at]
    column_details_list = [Media.id, Media.file, Media.file_type, Media.description, Media.is_active, Media.created_at, Media.updated_at, Media.texts]
    column_sortable_list = [Media.id, Media.file_type, Media.is_active, Media.created_at, Media.updated_at]
    column_searchable_list = [Media.id, Media.file_type, Media.description]
    column_filters = [Media.file_type, Media.is_active]

    form_columns = [Media.file, Media.file_type, Media.description, Media.is_active]

    name = "Media"
    name_plural = "Media Files"
    icon = "fa-solid fa-image"

    category = "Important Data"


    async def on_model_change(self, data, model, is_created, session):
        file = data.get('file')
        if isinstance(file, UploadFile):
            try:
                filename = await bot_storage.put(file)
                model.file = filename
            except Exception as e:
                log.error(f"Error uploading file: {e}")
                raise ValueError("Error uploading file")

    async def after_model_delete(self, model, session):
        try:
            await bot_storage.delete(model.file)
        except Exception as e:
            log.error(f"Error deleting file: {e}")
