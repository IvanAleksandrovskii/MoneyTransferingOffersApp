from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.models import db_helper, Currency, Country, TransferProvider, ProviderExchangeRate
from core.schemas import (
    CurrencyResponse, CountryResponse,
    ExchangeRateResponse
)
from core.services.get_object import get_object_by_name


router = APIRouter()


@router.get("/provider/{provider_name}/exchange-rates", response_model=List[ExchangeRateResponse], tags=["By Name"])
async def get_provider_exchange_rates_by_name(
        provider_name: str,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    provider = await get_object_by_name(session, TransferProvider, provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found with name: {provider_name}")

    query = (
        select(ProviderExchangeRate)
        .filter(ProviderExchangeRate.provider_id == provider.id)
        .options(
            joinedload(ProviderExchangeRate.provider),
            joinedload(ProviderExchangeRate.from_currency),
            joinedload(ProviderExchangeRate.to_currency)
        )
    )
    result = await session.execute(query)
    rates = result.unique().scalars().all()

    return [ExchangeRateResponse.model_validate(rate) for rate in rates]


@router.get("/currency/{currency_name}", response_model=CurrencyResponse, tags=["By Name"])
async def get_currency_by_name(
        currency_name: str,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    currency = await get_object_by_name(session, Currency, currency_name)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return CurrencyResponse.model_validate(currency)


@router.get("/country/{country_name}", response_model=CountryResponse, tags=["By Name"])
async def get_country_by_name(
        country_name: str,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    country = await get_object_by_name(session, Country, country_name)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return CountryResponse.model_validate(country)
