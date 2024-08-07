from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper, Country, Currency, TransferProvider, TransferRule, ProviderExchangeRate
from core.schemas import GenericObjectResponse


router = APIRouter()


# TODO: SUPER ENDPOINT - del (?) or keep it ?
@router.get("/object/{uuid}", response_model=GenericObjectResponse,
            summary="Get any object by UUID",
            description="This is a super function that can retrieve any object (Country, Currency, "
                        "TransferProvider, TransferRule, ProviderExchangeRate) by its UUID.")
async def get_object_by_uuid(
        uuid: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    for model in [Country, Currency, TransferProvider, TransferRule, ProviderExchangeRate]:
        obj = await session.get(model, uuid)
        if obj:
            # Extract data excluding SQLAlchemy fields
            data = {
                attr_name: getattr(obj, attr_name)
                for attr_name, column in inspect(model).mapper.column_attrs.items()
                if not attr_name.startswith('_')
            }
            return GenericObjectResponse(
                object_type=model.__name__,
                data=data
            )
    raise HTTPException(status_code=404, detail="Object not found")
