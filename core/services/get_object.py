from uuid import UUID

from async_lru import alru_cache
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core import logger, settings

# from sqlalchemy.orm import joinedload
# from core.models import Country


"""
Method down below is used now only with MAIN endpoint to get the currency object.
"""


@alru_cache(maxsize=settings.cache.objects_cached_max_count, ttl=settings.cache.objects_cache_sec)
async def get_object_by_id(session: AsyncSession, model, _id: UUID):
    """
    Retrieve an active object by its ID, using cache if available. Used only for MAIN endpoint (!)

    :param session: The database session
    :param model: The SQLAlchemy model class
    :param _id: The ID (UUID format) of the object to retrieve

    :return object: The retrieved object

    :exception: If the object is not found or is inactive
    """
    query = model.active().filter(model.id == _id)

    try:
        result = await session.execute(query)
        obj = result.unique().scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Error retrieving {model.__name__} with id: {_id}, detail={str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving {model.__name__} with id: {_id}")

    if obj:
        logger.info(f"Found active {model.__name__}: {obj.id}")
        return obj
    else:
        logger.warning(f"Active {model.__name__} not found for id: {_id}")
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found with id: {_id}")
