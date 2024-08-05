from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, aliased

from core.models import db_helper, Currency, Country, ProviderExchangeRate
from core.models import TransferRule
from core.models import TransferProvider
from core.schemas import ProviderResponse, TransferRequest, TransferRuleResponse

router = APIRouter()


@router.get("/providers", response_model=List[ProviderResponse])
async def get_providers(session: AsyncSession = Depends(db_helper.session_getter)):
    query = (
        select(TransferProvider)
        .filter(TransferProvider.is_active == True)
        .options(joinedload(TransferProvider.transfer_rules))
    )
    result = await session.execute(query)
    providers = result.unique().scalars().all()

    return [
        ProviderResponse(
            id=provider.id,
            name=provider.name,
            transfer_rules=[TransferRuleResponse.from_orm(rule) for rule in provider.transfer_rules]
        )
        for provider in providers
    ]


@router.get("/transfer-rules")
async def get_transfer_rules(
        send_country: str = Query(..., description="Name of the sending country"),
        receive_country: str = Query(..., description="Name of the receiving country"),
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
                SendCountry.name == send_country,
                ReceiveCountry.name == receive_country
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

    return [TransferRuleResponse.from_orm(rule) for rule in rules]


@router.post("/calculate-transfer")
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
    rule = result.unique().scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Transfer rule not found")

    src_currency = await session.execute(select(Currency).where(Currency.abbreviation == transfer.currency))
    src_currency = src_currency.scalar_one_or_none()

    if not src_currency:
        raise HTTPException(status_code=404, detail="Source currency not found")

    dst_currency = rule.transfer_currency

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
        raise HTTPException(status_code=404, detail="Exchange rate not found")

    converted_amount = transfer.amount * exchange_rate.rate

    if converted_amount < rule.min_transfer_amount or (
            rule.max_transfer_amount and converted_amount > rule.max_transfer_amount):
        raise HTTPException(status_code=400, detail="Transfer amount is out of allowed range")

    fee = converted_amount * (rule.fee_percentage / 100)

    response = {
        "source_currency": src_currency.abbreviation,
        "source_amount": transfer.amount,
        "destination_currency": dst_currency.abbreviation,
        "converted_amount": converted_amount,
        "exchange_rate": exchange_rate.rate,
        "fee_percentage": rule.fee_percentage,
        "fee_amount": fee,
        "total_amount": converted_amount + fee,
        "provider": rule.provider.name,
        "transfer_method": rule.transfer_method,
        "estimated_transfer_time": rule.estimated_transfer_time,
        "required_documents": rule.required_documents
    }

    return response
