from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import Country


async def get_object_by_id(session: AsyncSession, model, id: UUID):
    """
    Retrieve an active object by its ID.
    """
    query = model.active().filter(model.id == id)

    if model == Country:
        query = query.options(joinedload(Country.local_currency))

    result = await session.execute(query)
    obj = result.unique().scalar_one_or_none()

    if obj:
        logger.info(f"Found active {model.__name__}: {obj.id}")
    else:
        logger.warning(f"Active {model.__name__} not found for id: {id}")

    return obj


async def get_object_by_name(session: AsyncSession, model, name: str):
    """
    Retrieve an active object by its name.
    """
    if hasattr(model, 'name'):
        query = model.active().filter(model.name.ilike(f"%{name}%"))
    else:
        raise HTTPException(status_code=400, detail=f"Cannot search {model.__name__} by name")

    if model == Country:
        query = query.options(joinedload(Country.local_currency))

    result = await session.execute(query)
    obj = result.unique().scalar_one_or_none()

    if obj:
        logger.info(f"Found active {model.__name__}: {obj.name}")
    else:
        logger.warning(f"Active {model.__name__} not found for name: {name}")

    return obj
