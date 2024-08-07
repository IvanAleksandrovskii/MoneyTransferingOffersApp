from typing import List
from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.services.get_object import get_object_by_id
from core.models import db_helper, Currency, Country
from core.schemas import CurrencyResponse, CountryResponse


router = APIRouter()


@router.get("/currency/{currency_id}", response_model=CurrencyResponse, tags=["Global Objects"])
async def get_currency(
        currency_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    currency = await get_object_by_id(session, Currency, currency_id)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return CurrencyResponse.model_validate(currency)


@router.get("/currencies", response_model=List[CurrencyResponse], tags=["Global Objects"])
async def get_all_currencies(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(Currency)
    result = await session.execute(query)
    currencies = result.scalars().all()
    return [CurrencyResponse.model_validate(currency) for currency in currencies]


@router.get("/country/{country_id}", response_model=CountryResponse, tags=["Global Objects"])
async def get_country(
        country_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    country = await get_object_by_id(session, Country, country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return CountryResponse.model_validate(country)


@router.get("/countries", response_model=List[CountryResponse], tags=["Global Objects"])
async def get_all_countries(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(Country).options(joinedload(Country.local_currency))
    result = await session.execute(query)
    countries = result.unique().scalars().all()
    return [CountryResponse.model_validate(country) for country in countries]
