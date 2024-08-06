from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import Country, Currency


async def get_object_by_id(session: AsyncSession, model, id: UUID):
    query = select(model).filter(model.id == id)

    if model == Country:
        query = query.options(joinedload(Country.local_currency))

    result = await session.execute(query)
    obj = result.unique().scalar_one_or_none()

    if obj:
        logger.info(f"Found {model.__name__}: {obj.id}")
    else:
        logger.warning(f"{model.__name__} not found for id: {id}")

    return obj


async def get_object_by_name(session: AsyncSession, model, name: str):
    if model == Currency:
        query = select(model).filter(or_(model.name == name, model.abbreviation == name))
    elif hasattr(model, 'name'):
        query = select(model).filter(model.name == name)
    else:
        raise HTTPException(status_code=400, detail=f"Cannot search {model.__name__} by name")

    if model == Country:
        query = query.options(joinedload(Country.local_currency))

    result = await session.execute(query)
    obj = result.unique().scalar_one_or_none()

    if obj:
        logger.info(f"Found {model.__name__}: {obj.name}")
    else:
        logger.warning(f"{model.__name__} not found for name: {name}")

    return obj
