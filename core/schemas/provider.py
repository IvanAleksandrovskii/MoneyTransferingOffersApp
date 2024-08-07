from .base import BaseResponse


class ProviderResponse(BaseResponse):
    name: str
    url: str | None  # TODO: str only if nullable is False in the model
