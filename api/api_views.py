from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.models import db_helper, Currency, Country, ProviderExchangeRate
from core.models.transfer_rule import TransferRule
from core.models.transfer_provider import TransferProvider
from core.schemas import ProviderResponse, TransferRequest, TransferRuleResponse

router = APIRouter()


@router.get("/providers")
async def get_providers(session: AsyncSession = Depends(db_helper.session_getter)):
    providers = await session.execute(select(TransferProvider).filter(TransferProvider.is_active == True))
    return providers.scalars().all()


@router.get("/transfer-rules")
async def get_transfer_rules(
    from_country: str,
    to_country: str,
    amount: float,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    rules = await session.execute(
        select(TransferRule).filter(
            TransferRule.send_country.has(name=from_country, is_active=True),
            TransferRule.receive_country.has(name=to_country, is_active=True),
            TransferRule.min_transfer_amount <= amount,
            TransferRule.max_transfer_amount >= amount,
            TransferRule.is_active == True
        )
    )
    return rules.scalars().all()


# TODO: add pagination (?)
@router.post("/transfer-options", response_model=List[ProviderResponse])
async def get_transfer_options(
        request: TransferRequest,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    from_country = await session.execute(
        select(Country).filter(Country.name == request.from_country, Country.is_active == True))
    from_country = from_country.scalar_one_or_none()
    if not from_country:
        raise HTTPException(status_code=404, detail="From country not found")

    to_country = await session.execute(
        select(Country).filter(Country.name == request.to_country, Country.is_active == True))
    to_country = to_country.scalar_one_or_none()
    if not to_country:
        raise HTTPException(status_code=404, detail="To country not found")

    currency = await session.execute(
        select(Currency).filter(Currency.abbreviation == request.currency, Currency.is_active == True))
    currency = currency.scalar_one_or_none()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    # Get RUB currency
    rub_currency = await session.execute(select(Currency).filter(Currency.abbreviation == "RUB", Currency.is_active == True))
    rub_currency = rub_currency.scalar_one_or_none()
    if not rub_currency:
        raise HTTPException(status_code=404, detail="RUB currency not found")

    # Get transfer rules, filter by requested params
    query = select(TransferRule).options(
        joinedload(TransferRule.provider),
        joinedload(TransferRule.transfer_currency)
    ).filter(
        TransferRule.send_country_id == from_country.id,
        TransferRule.receive_country_id == to_country.id,
        TransferRule.is_active == True,
        TransferRule.provider.has(is_active=True),
        or_(
            TransferRule.transfer_currency_id == None,
            TransferRule.transfer_currency.has(is_active=True)
        ),
        TransferRule.send_country.has(is_active=True),
        TransferRule.receive_country.has(is_active=True)
    )

    result = await session.execute(query)
    transfer_rules = result.unique().scalars().all()

    providers = {}
    for rule in transfer_rules:
        rule_currency = rule.transfer_currency or rub_currency

        # Get exchange rate for the requested currencies and provider
        exchange_rate = await session.execute(
            select(ProviderExchangeRate).filter(
                and_(
                    ProviderExchangeRate.provider_id == rule.provider_id,
                    ProviderExchangeRate.from_currency_id == currency.id,
                    ProviderExchangeRate.to_currency_id == rule_currency.id
                )
            )
        )
        exchange_rate = exchange_rate.scalar_one_or_none()

        if not exchange_rate:
            continue  # Skips all another rules if there is no exchange rate

        # Convert requested amount to requested currency
        converted_amount = request.amount * exchange_rate.rate

        # Check if the rule is applicable
        if rule.min_transfer_amount <= converted_amount and (
                rule.max_transfer_amount is None or converted_amount <= rule.max_transfer_amount):
            if rule.provider.id not in providers:
                providers[rule.provider.id] = ProviderResponse(
                    id=rule.provider_id,
                    name=rule.provider.name,
                    transfer_rules=[]
                )

            providers[rule.provider.id].transfer_rules.append(TransferRuleResponse(
                id=rule.id,
                transfer_currency=rule_currency.abbreviation,
                fee_percentage=rule.fee_percentage,
                min_transfer_amount=rule.min_transfer_amount,
                max_transfer_amount=rule.max_transfer_amount,
                transfer_method=rule.transfer_method,
                estimated_transfer_time=rule.estimated_transfer_time,
                required_documents=rule.required_documents,
                exchange_rate=exchange_rate.rate
            ))

    return list(providers.values())
