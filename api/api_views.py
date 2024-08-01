from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.models import db_helper, Currency, Country
from core.models.transfer_rule import TransferRule
from core.models.transfer_provider import TransferProvider
from core.schemas import ProviderResponse, TransferRequest, TransferRuleResponse

router = APIRouter()


@router.get("/providers")
async def get_providers(session: AsyncSession = Depends(db_helper.session_getter)):
    providers = await session.execute(select(TransferProvider))
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
            TransferRule.send_country.has(name=from_country),
            TransferRule.receive_country.has(name=to_country),
            TransferRule.min_transfer_amount <= amount,
            TransferRule.max_transfer_amount >= amount
        )
    )
    return rules.scalars().all()


# TODO: add pagination (?)
@router.post("/transfer-options", response_model=List[ProviderResponse])
async def get_transfer_options(
        request: TransferRequest,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    # Get country and currency ID
    from_country = await session.execute(select(Country).filter(Country.name == request.from_country))
    from_country = from_country.scalar_one_or_none()
    if not from_country:
        raise HTTPException(status_code=404, detail="From country not found")

    to_country = await session.execute(select(Country).filter(Country.name == request.to_country))
    to_country = to_country.scalar_one_or_none()
    if not to_country:
        raise HTTPException(status_code=404, detail="To country not found")

    currency = await session.execute(select(Currency).filter(Currency.abbreviation == request.currency))
    currency = currency.scalar_one_or_none()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    # Get transfer rules, filter by requested params
    query = select(TransferRule).options(
        joinedload(TransferRule.provider),
        joinedload(TransferRule.transfer_currency)
    ).filter(
        TransferRule.send_country_id == from_country.id,
        TransferRule.receive_country_id == to_country.id,
        TransferRule.transfer_currency_id == currency.id,
        TransferRule.min_transfer_amount <= request.amount,
        TransferRule.max_transfer_amount >= request.amount
        # TODO: Check logic here, cause if min is 0 than I can transfer 0? Absolutely not. Than mb need to
        #     add some validation logic (?), like "amount should be more than 0"
    )

    result = await session.execute(query)
    transfer_rules = result.unique().scalars().all()

    # Group transfer rules by provider
    providers = {}
    for rule in transfer_rules:
        if rule.provider.id not in providers:
            providers[rule.provider.id] = ProviderResponse(
                id=rule.provider.id,
                name=rule.provider.name,
                # url=rule.provider.url,
                transfer_rules=[]
            )

        # TODO: Idea, can use something like this to control communication with AI if we add in the future
        #     or we can use it in the frontend for example
        highlights = []

        # Transfer speed highlights
        speed_keywords = [
            "instant", "моментально", "срочный", "срочно", "momentum",
            "быстро", "быстрый", "экспресс", "мгновенно", "немедленно",
            "quick", "fast", "immediate"
        ]
        if rule.fee_percentage == 0:
            highlights.append("No fee")
        elif rule.fee_percentage < 1:
            highlights.append("Low fee")

        transfer_time_lower = rule.estimated_transfer_time.lower()

        if any(keyword in transfer_time_lower for keyword in speed_keywords):
            highlights.append("Fast transfer")

        providers[rule.provider.id].transfer_rules.append(TransferRuleResponse(
            id=rule.id,
            transfer_currency=rule.transfer_currency.abbreviation,
            fee_percentage=rule.fee_percentage,
            min_transfer_amount=rule.min_transfer_amount,
            max_transfer_amount=rule.max_transfer_amount,
            transfer_method=rule.transfer_method,
            estimated_transfer_time=rule.estimated_transfer_time,
            required_documents=rule.required_documents,
            highlights=highlights
        ))

    return list(providers.values())
