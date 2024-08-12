from .base import BaseResponse


class ProviderResponse(BaseResponse):
    name: str
    url: str
