from typing import Optional

from .base import BaseResponse


class ProviderResponse(BaseResponse):
    name: str
    url: str
    logo: Optional[str]

    @classmethod
    def model_validate(cls, obj, **kwargs):
        logo_path = obj.logo
        if logo_path and logo_path.startswith("/app/"):
            logo_path = logo_path[4:]  # Remove "/app" prefix

        return cls(
            id=obj.id,
            name=obj.name,
            url=obj.url,
            logo=logo_path
        )
