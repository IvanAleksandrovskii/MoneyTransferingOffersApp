from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger, cache
from core.models import Country


async def get_object_by_id(session: AsyncSession, model, _id: UUID):
    """
    Retrieve an active object by its ID, using cache if available.

    :param session: The database session
    :param model: The SQLAlchemy model class
    :param _id: The ID (UUID format) of the object to retrieve

    :return object: The retrieved object

    :exception: If the object is not found or is inactive
    """
    cache_key = f"{model.__name__}:{_id}"
    cached_obj = await cache.get(cache_key)

    if cached_obj:
        logger.info(f"Retrieved {model.__name__} {_id} from cache")
        return model(**cached_obj)

    query = model.active().filter(model.id == _id)

    if model == Country:
        query = query.options(joinedload(Country.local_currency))

    result = await session.execute(query)
    obj = result.unique().scalar_one_or_none()

    if obj:
        logger.info(f"Found active {model.__name__}: {obj.id}")
        # Manually serialize the object to a dictionary
        obj_dict = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        await cache.set(cache_key, obj_dict)  # Cache the serialized dictionary
    else:
        logger.warning(f"Active {model.__name__} not found for id: {_id}")
        raise HTTPException(model.__name__, str(_id))

    return obj
