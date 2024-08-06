from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, aliased, selectinload

from core.models import db_helper, Currency, Country, ProviderExchangeRate
from core.models import TransferRule
from core.models import TransferProvider
from core.schemas import ProviderResponse, TransferRequest, TransferRuleResponse, TransferResponse, \
    TransferRuleByCountriesRequest

router = APIRouter()


@router.get("/providers", response_model=List[ProviderResponse])
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

    return [
        ProviderResponse(
            id=provider.id,
            name=provider.name,
            transfer_rules=[
                f"{rule.send_country.name}-{rule.receive_country.name}-{rule.transfer_currency.abbreviation}-{rule.min_transfer_amount}-{rule.max_transfer_amount}-{rule.id}"
                for rule in provider.transfer_rules
            ]
        )
        for provider in providers
    ]


@router.post("/transfer-rules-by-countries", response_model=List[TransferRuleResponse])
async def get_transfer_rules(
    transfer: TransferRuleByCountriesRequest,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    SendCountry = aliased(Country)
    ReceiveCountry = aliased(Country)

    query = (
        select(TransferRule)
        .join(SendCountry, TransferRule.send_country_id == SendCountry.id)
        .join(ReceiveCountry, TransferRule.receive_country_id == ReceiveCountry.id)
        .where(
            and_(
                SendCountry.name == transfer.send_country,
                ReceiveCountry.name == transfer.receive_country
            )
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
        raise HTTPException(status_code=404, detail="No transfer rules found for the specified countries")

    return [TransferRuleResponse.from_orm(rule) for rule in rules]


@router.post("/calculate-transfer", response_model=List[TransferResponse])
async def calculate_transfer(
    transfer: TransferRequest,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    SendCountry = aliased(Country)
    ReceiveCountry = aliased(Country)

    query = (
        select(TransferRule)
        .join(SendCountry, TransferRule.send_country_id == SendCountry.id)
        .join(ReceiveCountry, TransferRule.receive_country_id == ReceiveCountry.id)
        .where(
            and_(
                SendCountry.name == transfer.send_country,
                ReceiveCountry.name == transfer.receive_country
            )
        )
        .options(
            joinedload(TransferRule.provider),
            joinedload(TransferRule.transfer_currency)
        )
    )

    result = await session.execute(query)
    rules = result.unique().scalars().all()

    if not rules:
        raise HTTPException(status_code=404, detail="No transfer rules found")

    src_currency = await session.execute(select(Currency).where(Currency.abbreviation == transfer.currency))
    src_currency = src_currency.scalar_one_or_none()

    if not src_currency:
        raise HTTPException(status_code=404, detail="Source currency not found")

    responses = []

    for rule in rules:
        dst_currency = rule.transfer_currency

        if src_currency.id != dst_currency.id:
            exchange_rate_query = select(ProviderExchangeRate).where(
                and_(
                    ProviderExchangeRate.provider_id == rule.provider_id,
                    ProviderExchangeRate.from_currency_id == src_currency.id,
                    ProviderExchangeRate.to_currency_id == dst_currency.id
                )
            )
            exchange_rate = await session.execute(exchange_rate_query)
            exchange_rate = exchange_rate.scalar_one_or_none()

            if not exchange_rate:
                continue

            converted_amount = transfer.amount * exchange_rate.rate
        else:
            converted_amount = transfer.amount
            exchange_rate = None

        if converted_amount < rule.min_transfer_amount or (
                rule.max_transfer_amount and converted_amount > rule.max_transfer_amount):
            continue

        fee = converted_amount * (rule.fee_percentage / 100)
        transfer_amount = converted_amount - fee

        response = {
            "source_currency": src_currency.abbreviation,
            "source_amount": transfer.amount,
            "destination_currency": dst_currency.abbreviation,
            "converted_amount": converted_amount,
            "exchange_rate": exchange_rate.rate if exchange_rate else 1.0,
            "fee_percentage": rule.fee_percentage,
            "fee_amount": fee,
            "transfer_amount": transfer_amount,
            "provider": rule.provider.name,
            "transfer_method": rule.transfer_method,
            "estimated_time": rule.estimated_transfer_time,
            "required_docs": rule.required_documents
        }

        responses.append(response)

    if not responses:
        raise HTTPException(status_code=404, detail="No suitable transfer rules found")

    return responses
