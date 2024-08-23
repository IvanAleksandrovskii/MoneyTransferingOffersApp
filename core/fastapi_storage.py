from fastapi_storages import FileSystemStorage
from core import settings

storage = FileSystemStorage(path=settings.media.root)
