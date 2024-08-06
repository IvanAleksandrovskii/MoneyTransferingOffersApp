from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import logger
from core.models import Currency


async def get_currency_by_abbreviation(session: AsyncSession, abbreviation: str) -> Currency:
    query = select(Currency).filter(Currency.abbreviation == abbreviation)
    result = await session.execute(query)
    currency = result.scalar_one_or_none()
    if not currency:
        logger.warning(f"Currency not found for abbreviation: {abbreviation}")
        raise HTTPException(status_code=404, detail=f"Currency not found for abbreviation: {abbreviation}")
    return currency
