# services/fastapi_storage.py

import os

from fastapi import UploadFile
from fastapi_storages import FileSystemStorage

from core import settings


# TODO: ADD old media deletion on media change
class CustomFileSystemStorage(FileSystemStorage):
    def __init__(self, root_path: str):
        self.root_path = root_path
        super().__init__(self.root_path)

    async def put(self, file: UploadFile) -> str:
        os.makedirs(self.root_path, exist_ok=True)
        full_path = os.path.join(self.root_path, file.filename)

        content = await file.read()
        with open(full_path, "wb") as f:
            f.write(content)

        return file.filename

    def delete(self, name: str) -> None:
        # TODO: Doublecheck (( ! ))
        if name.startswith("media/"):
            name = name[6:]
        if name.startswith("bot/"):
            name = name[4:]
        full_path = os.path.join(self.root_path, name)
        if os.path.exists(full_path):
            os.remove(full_path)


storage = CustomFileSystemStorage(root_path=settings.media.root)
bot_storage = CustomFileSystemStorage(root_path=settings.media.bot)
