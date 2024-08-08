from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferProvider, ProviderExchangeRate, TransferRule
from core.schemas import (
    CurrencyResponse, CountryResponse,
    ExchangeRateResponse, DetailedTransferRuleResponse, ProviderResponse
)
from core.services import get_object_by_name


router = APIRouter()


@router.get("/transfer-rules-by-countries", response_model=List[DetailedTransferRuleResponse])
async def get_transfer_rules_by_countries(
    send_country: Optional[str] = Query(..., description="ID or name of the sending country"),
    receive_country: Optional[str] = Query(..., description="ID or name of the receiving country"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    if not send_country or not receive_country:
        raise HTTPException(status_code=400, detail="Send country and receive country are required")

    logger.info(f"Searching for transfer rules: from {send_country} to {receive_country}")

    send_country = await get_object_by_name(session, Country, send_country)
    receive_country = await get_object_by_name(session, Country, receive_country)

    if not send_country or not receive_country:
        logger.error(f"Country not found. Send country: {send_country}, Receive country: {receive_country}")
        raise HTTPException(status_code=404, detail="Country not found")

    logger.info(f"Found countries: from {send_country.name} (ID: {send_country.id}) to {receive_country.name} (ID: {receive_country.id})")

    query = (
        select(TransferRule)
        .filter(
            TransferRule.send_country_id == send_country.id,
            TransferRule.receive_country_id == receive_country.id
        )
        .options(
            joinedload(TransferRule.send_country),
            joinedload(TransferRule.receive_country),
            joinedload(TransferRule.provider),
            joinedload(TransferRule.transfer_currency)
        )
    )

    result = await session.execute(query)
    rules = result.unique().scalars().all()

    if not rules:
        logger.warning(f"No transfer rules found for countries: from {send_country.name} to {receive_country.name}")
        raise HTTPException(status_code=404, detail="No transfer rules found for the specified countries")

    logger.info(f"Found {len(rules)} transfer rules")

    return [DetailedTransferRuleResponse.model_validate(rule) for rule in rules]


@router.get("/provider/rules", response_model=List[DetailedTransferRuleResponse])
async def get_provider_rules_by_name(
        provider_name: Optional[str] = Query(..., description="Name of the provider"),
        session: AsyncSession = Depends(db_helper.session_getter)
):
    if not provider_name:
        raise HTTPException(status_code=400, detail="Provider name is required")

    logger.debug(f"Searching for transfer rules for provider: {provider_name}")
    provider = await get_object_by_name(session, TransferProvider, provider_name)
    if not provider:
        logger.debug(f"Provider not found with name: {provider_name}")
        raise HTTPException(status_code=404, detail="Provider not found")

    query = select(TransferRule).filter(TransferRule.provider_id == provider.id).options(
        joinedload(TransferRule.send_country),
        joinedload(TransferRule.receive_country),
        joinedload(TransferRule.provider),
        joinedload(TransferRule.transfer_currency)
    )
    result = await session.execute(query)
    rules = result.scalars().all()

    return [DetailedTransferRuleResponse.model_validate(rule) for rule in rules]


@router.get("/provider/exchange-rates", response_model=List[ExchangeRateResponse], tags=["By Name"])
async def get_provider_exchange_rates_by_name(
        provider_name: Optional[str] = Query(..., description="Name of the provider"),
        session: AsyncSession = Depends(db_helper.session_getter)
):
    if not provider_name:
        raise HTTPException(status_code=400, detail="Provider name is required")

    logger.debug(f"Searching for exchange rates for provider: {provider_name}")
    provider = await get_object_by_name(session, TransferProvider, provider_name)
    if not provider:
        logger.debug(f"Provider not found with name: {provider_name}")
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

    return [ExchangeRateResponse(
        id=rate.id,
        provider=ProviderResponse(
            id=rate.provider.id,
            name=rate.provider.name,
            url=rate.provider.url  # Added url, don't forget to add a new field here next time too
        ),
        from_currency=CurrencyResponse.model_validate(rate.from_currency),
        to_currency=CurrencyResponse.model_validate(rate.to_currency),
        rate=rate.rate,
        last_updated=rate.last_updated
    ) for rate in rates]


@router.get("/currency/by-name", response_model=CurrencyResponse, tags=["By Name"])
async def get_currency_by_name(
    currency_name: str = Query(..., description="Name of the currency"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    if not currency_name:
        logger.debug(f"Currency name is required: {currency_name}")
        raise HTTPException(status_code=400, detail="Currency name is required")
    currency = await get_object_by_name(session, Currency, currency_name)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return CurrencyResponse.model_validate(currency)


@router.get("/currency/by-abbreviation", response_model=CurrencyResponse, tags=["By Name"])
async def get_currency_by_abbreviation(
    currency_abbreviation: str = Query(..., description="Abbreviation of the currency"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    if not currency_abbreviation:
        logger.debug(f"Currency abbreviation is required: {currency_abbreviation}")
        raise HTTPException(status_code=400, detail="Currency abbreviation is required")
    currency = await get_currency_by_abbreviation(session=session, currency_abbreviation=currency_abbreviation)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return CurrencyResponse.model_validate(currency)


@router.get("/country", response_model=CountryResponse, tags=["By Name"])
async def get_country_by_name(
        country_name: Optional[str] = Query(..., description="Name of the country"),
        session: AsyncSession = Depends(db_helper.session_getter)
):
    if not country_name:
        logger.debug(f"Country name is required: {country_name}")
        raise HTTPException(status_code=400, detail="Country name is required")
    logger.debug(f"Searching for country: {country_name}")
    country = await get_object_by_name(session, Country, country_name)
    if not country_name:
        logger.debug(f"Country name is required: {country_name}")
        raise HTTPException(status_code=404, detail="Country name is required")
    if not country:
        logger.debug(f"Country not found: {country_name}")
        raise HTTPException(status_code=404, detail="Country not found")
    return CountryResponse.model_validate(country)
