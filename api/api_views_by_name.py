from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferProvider, ProviderExchangeRate, TransferRule
from core.schemas import (
    CurrencyResponse, CountryResponse,
    ExchangeRateResponse, DetailedTransferRuleResponse, TransferRuleRequestByName, ProviderResponse
)
from core.services.get_object import get_object_by_name


router = APIRouter()


@router.post("/transfer-rules-by-country-names", response_model=List[DetailedTransferRuleResponse], tags=["By Name"])
async def get_transfer_rules_by_country_names(
    transfer: TransferRuleRequestByName,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    logger.info(f"Searching for transfer rules: from {transfer.send_country} to {transfer.receive_country}")

    send_country = await get_object_by_name(session, Country, transfer.send_country)
    receive_country = await get_object_by_name(session, Country, transfer.receive_country)

    if not send_country or not receive_country:
        logger.error(f"Country not found. Send country: {transfer.send_country}, Receive country: {transfer.receive_country}")
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


@router.get("/provider/{provider_name}/rules", response_model=List[DetailedTransferRuleResponse])
async def get_provider_rules_by_name(
        provider_name: str,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    provider = await get_object_by_name(session, TransferProvider, provider_name)
    if not provider:
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
