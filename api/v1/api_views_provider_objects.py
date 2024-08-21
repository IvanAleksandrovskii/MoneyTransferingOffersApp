from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, TransferProvider, TransferRule, ProviderExchangeRate, Country, Currency
from core.schemas import ProviderResponse, ExchangeRateResponse, DetailedTransferRuleResponse
from utils import Ordering

router = APIRouter()

provider_ordering = Ordering(TransferProvider, ["id", "name", "url"])
transfer_rule_ordering = Ordering(TransferRule, [
    "id", "fee_percentage", "min_transfer_amount", "max_transfer_amount",
    "transfer_method", "min_transfer_time", "max_transfer_time",
    "send_country_id", "receive_country_id", "provider_id", "transfer_currency_id"
])
exchange_rate_ordering = Ordering(ProviderExchangeRate, [
    "id", "rate", "last_updated", "provider_id", "from_currency_id", "to_currency_id"
])


@router.get("/providers", response_model=List[ProviderResponse])
async def get_all_providers(
        session: AsyncSession = Depends(db_helper.session_getter),
        order: Optional[str] = Query(None),
        order_desc: bool = Query(False)
):
    query = TransferProvider.active().order_by(provider_ordering.order_by(order, order_desc))
    try:
        result = await session.execute(query)
        providers = result.scalars().all()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_all_providers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [ProviderResponse.model_validate(provider) for provider in providers]


@router.get("/provider/{provider_id}", response_model=ProviderResponse)
async def get_provider(
        provider_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    query = TransferProvider.active().where(TransferProvider.id == provider_id)
    try:
        result = await session.execute(query)
        provider = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_provider: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return ProviderResponse.model_validate(provider)


@router.get("/transfer-rules", response_model=List[DetailedTransferRuleResponse])
async def get_all_transfer_rules(
        session: AsyncSession = Depends(db_helper.session_getter),
        order: Optional[str] = Query(None),
        order_desc: bool = Query(False)
):
    query = (
        TransferRule.active()
        .options(
            joinedload(TransferRule.send_country).joinedload(Country.local_currency),
            joinedload(TransferRule.receive_country).joinedload(Country.local_currency),
            joinedload(TransferRule.provider),
            joinedload(TransferRule.transfer_currency),
            joinedload(TransferRule.required_documents)
        )
        .filter(
            TransferRule.provider.has(TransferProvider.is_active == True),
            TransferRule.send_country.has(Country.is_active == True),
            TransferRule.receive_country.has(Country.is_active == True),
            TransferRule.transfer_currency.has(Currency.is_active == True)
        )
        .order_by(transfer_rule_ordering.order_by(order, order_desc))
    )
    try:
        result = await session.execute(query)
        transfer_rules = result.unique().scalars().all()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_all_transfer_rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [DetailedTransferRuleResponse.model_validate(rule) for rule in transfer_rules]


@router.get("/transfer-rule/{transfer_rule_id}", response_model=DetailedTransferRuleResponse)
async def get_transfer_rule(transfer_rule_id: UUID, session: AsyncSession = Depends(db_helper.session_getter)):
    query = (
        TransferRule.active()
        .where(TransferRule.id == transfer_rule_id)
        .options(
            joinedload(TransferRule.send_country).joinedload(Country.local_currency),
            joinedload(TransferRule.receive_country).joinedload(Country.local_currency),
            joinedload(TransferRule.provider),
            joinedload(TransferRule.transfer_currency),
            joinedload(TransferRule.required_documents)
        )
        .filter(
            TransferRule.provider.has(TransferProvider.is_active == True),
            TransferRule.send_country.has(Country.is_active == True),
            TransferRule.receive_country.has(Country.is_active == True),
            TransferRule.transfer_currency.has(Currency.is_active == True)
        )
    )
    try:
        result = await session.execute(query)
        transfer_rule = result.unique().scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_transfer_rule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not transfer_rule:
        raise HTTPException(status_code=404, detail="Transfer rule not found")

    return DetailedTransferRuleResponse.model_validate(transfer_rule)


@router.get("/exchange-rates", response_model=List[ExchangeRateResponse])
async def get_all_exchange_rates(
        session: AsyncSession = Depends(db_helper.session_getter),
        order: Optional[str] = Query(None),
        order_desc: bool = Query(False)
):
    query = (
        ProviderExchangeRate.active()
        .options(
            joinedload(ProviderExchangeRate.provider),
            joinedload(ProviderExchangeRate.from_currency),
            joinedload(ProviderExchangeRate.to_currency)
        )
        .filter(
            ProviderExchangeRate.provider.has(TransferProvider.is_active == True),
            ProviderExchangeRate.from_currency.has(Currency.is_active == True),
            ProviderExchangeRate.to_currency.has(Currency.is_active == True)
        )
        .order_by(exchange_rate_ordering.order_by(order, order_desc))
    )
    try:
        result = await session.execute(query)
        exchange_rates = result.unique().scalars().all()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_all_exchange_rates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [ExchangeRateResponse.model_validate(rate) for rate in exchange_rates]


@router.get("/exchange-rate/{exchange_rate_id}", response_model=ExchangeRateResponse)
async def get_exchange_rate(
        exchange_rate_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    query = (
        ProviderExchangeRate.active()
        .where(ProviderExchangeRate.id == exchange_rate_id)
        .options(
            joinedload(ProviderExchangeRate.provider),
            joinedload(ProviderExchangeRate.from_currency),
            joinedload(ProviderExchangeRate.to_currency)
        )
        .filter(
            ProviderExchangeRate.provider.has(TransferProvider.is_active == True),
            ProviderExchangeRate.from_currency.has(Currency.is_active == True),
            ProviderExchangeRate.to_currency.has(Currency.is_active == True)
        )
    )
    try:
        result = await session.execute(query)
        exchange_rate = result.unique().scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_exchange_rate: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not exchange_rate:
        raise HTTPException(status_code=404, detail="Exchange rate not found")

    return ExchangeRateResponse.model_validate(exchange_rate)
