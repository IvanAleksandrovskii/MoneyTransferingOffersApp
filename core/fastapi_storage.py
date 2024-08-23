import os
from fastapi_storages import FileSystemStorage
from core import settings


class CustomFileSystemStorage(FileSystemStorage):
    def delete(self, name: str) -> None:
        """
        Delete a file from the file system.
        """
        full_path = self.get_path(name)
        if os.path.exists(full_path):
            os.remove(full_path)


storage = CustomFileSystemStorage(path=settings.media.root)
