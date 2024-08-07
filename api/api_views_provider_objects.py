from typing import List
from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from core.services import get_object_by_id
from core.models import db_helper, TransferProvider, TransferRule, ProviderExchangeRate
from core.schemas import ProviderResponse, ExchangeRateResponse, CurrencyResponse, DetailedTransferRuleResponse

router = APIRouter()


@router.get("/providers", response_model=List[ProviderResponse], tags=["Provider Objects"])
async def get_providers(session: AsyncSession = Depends(db_helper.session_getter)):
    query = (
        select(TransferProvider)
        .filter(TransferProvider.is_active == True)
        .options(selectinload(TransferProvider.transfer_rules).selectinload(TransferRule.send_country))
        .options(selectinload(TransferProvider.transfer_rules).selectinload(TransferRule.receive_country))
        .options(selectinload(TransferProvider.transfer_rules).selectinload(TransferRule.transfer_currency))
    )
    result = await session.execute(query)
    providers = result.unique().scalars().all()

    return [ProviderResponse(id=provider.id, name=provider.name, url=provider.url) for provider in providers]


@router.get("/provider/{provider_id}/rules", response_model=List[DetailedTransferRuleResponse])
async def get_provider_rules_by_id(
        provider_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    provider = await get_object_by_id(session, TransferProvider, provider_id)
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


@router.get("/transfer-rules", response_model=List[DetailedTransferRuleResponse], tags=["Provider Objects"])
async def get_all_transfer_rules(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(TransferRule).options(
        joinedload(TransferRule.send_country),
        joinedload(TransferRule.receive_country),
        joinedload(TransferRule.provider),
        joinedload(TransferRule.transfer_currency)
    )
    result = await session.execute(query)
    rules = result.unique().scalars().all()

    return [DetailedTransferRuleResponse.model_validate(rule) for rule in rules]


@router.get("/provider/{provider_id}/exchange-rates", response_model=List[ExchangeRateResponse], tags=["Provider Objects"])
async def get_provider_exchange_rates(
        provider_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    provider = await get_object_by_id(session, TransferProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found with id: {provider_id}")

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

    return [
        ExchangeRateResponse(
            id=rate.id,
            provider=ProviderResponse(
                id=provider.id,
                name=provider.name,
                url=provider.url  # Added url, don't forget to add a new field here next time too
            ),
            from_currency=CurrencyResponse.model_validate(rate.from_currency),
            to_currency=CurrencyResponse.model_validate(rate.to_currency),
            rate=rate.rate,
            last_updated=rate.last_updated
        )
        for rate in rates
    ]


@router.get("/exchange-rates", response_model=List[ExchangeRateResponse], tags=["Provider Objects"])
async def get_all_exchange_rates(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(ProviderExchangeRate).options(
        joinedload(ProviderExchangeRate.provider),
        joinedload(ProviderExchangeRate.from_currency),
        joinedload(ProviderExchangeRate.to_currency)
    )
    result = await session.execute(query)
    rates = result.scalars().all()
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
