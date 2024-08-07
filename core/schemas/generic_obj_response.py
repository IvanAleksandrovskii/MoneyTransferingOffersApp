from typing import Any

from pydantic import BaseModel, ConfigDict


class GenericObjectResponse(BaseModel):
    object_type: str
    data: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
