from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferRule
from core.schemas import (
    OptimizedTransferRuleResponse, TransferRuleDetails, DetailedTransferRuleResponse,
    CurrencyResponse, CountryResponse, ProviderResponse,
)
from core.services import CurrencyConversionService
from core.services import get_object_by_id


router = APIRouter()


# TODO: Currency-USD-currency transfer options search not working NEED TO FIX

@router.get("/transfer-rules/{send_country_id}/{receive_country_id}", response_model=List[DetailedTransferRuleResponse])
async def get_transfer_rules_by_countries(
    send_country: UUID,
    receive_country: UUID,
    session: AsyncSession = Depends(db_helper.session_getter)
):

    # send_country = await get_object_by_id(session, Country, send_country)
    # receive_country = await get_object_by_id(session, Country, receive_country)

    # if not send_country or not receive_country:
    #     logger.debug(f"Send country and receive country are required. Send country: {send_country}, "
    #                  f"Receive country: {receive_country}")
    #     raise HTTPException(status_code=404, detail="Send country and receive country are required")

    logger.info(f"Searching for transfer rules: from {send_country} to {receive_country}")

    query = (
        select(TransferRule)
        .filter(
            TransferRule.send_country_id == send_country,
            TransferRule.receive_country_id == receive_country
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
        logger.warning(f"No transfer rules found for countries: from {send_country} to {receive_country}")
        raise HTTPException(status_code=404, detail="No transfer rules found for the specified countries")

    logger.info(f"Found {len(rules)} transfer rules")

    return [DetailedTransferRuleResponse.model_validate(rule) for rule in rules]


# Метод для проверки, подходит ли сумма под ограничения
def is_within_transfer_limits(converted_amount: float, rule) -> bool:
    return rule.min_transfer_amount <= converted_amount <= rule.max_transfer_amount


@router.get("/transfer-rules-full-filled-info/{send_country_id}/{receive_country_id}/{from_currency_id}", response_model=OptimizedTransferRuleResponse)
async def get_transfer_rules_full_filled_info(
    send_country_id: UUID,
    receive_country_id: UUID,
    from_currency_id: UUID,
    amount: float | None = Query(None, description="Amount to transfer", gt=0),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    # if not send_country_id or not receive_country_id or not from_currency_id:
    #     raise HTTPException(status_code=400, detail="Send country, receive country, and from currency are required")

    query = (
        select(TransferRule)
        .options(
            joinedload(TransferRule.send_country).joinedload(Country.local_currency),
            joinedload(TransferRule.receive_country).joinedload(Country.local_currency),
            joinedload(TransferRule.provider),
            joinedload(TransferRule.transfer_currency)
        )
        .filter(
            and_(
                TransferRule.send_country_id == send_country_id,
                TransferRule.receive_country_id == receive_country_id
            )
        )
    )

    result = await session.execute(query)
    rules = result.unique().scalars().all()

    if not rules:
        logger.info(f"No transfer rules found for countries: from {send_country_id} to {receive_country_id}")
        raise HTTPException(status_code=404, detail="No transfer rules found for the specified countries")

    from_currency = await get_object_by_id(session, Currency, from_currency_id)
    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    rule_details = []
    for rule in rules:
        try:
            converted_amount, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                session=session,
                amount=amount,
                from_currency=from_currency,
                to_currency=rule.transfer_currency,
                provider=rule.provider
            )

            if rule.min_transfer_amount <= converted_amount <= rule.max_transfer_amount:
                fee_percentage = rule.fee_percentage / 100
                transfer_fee = round(converted_amount * fee_percentage, 2)
                amount_received = round(converted_amount - transfer_fee, 2)

                rule_detail = TransferRuleDetails(
                    id=rule.id,
                    provider=ProviderResponse.model_validate(rule.provider),
                    transfer_method=rule.transfer_method,
                    estimated_transfer_time=rule.estimated_transfer_time,
                    required_documents=rule.required_documents,
                    original_amount=amount,
                    converted_amount=converted_amount,
                    transfer_currency=CurrencyResponse.model_validate(rule.transfer_currency),
                    amount_received=amount_received,
                    transfer_fee=transfer_fee,
                    transfer_fee_percentage=rule.fee_percentage,
                    min_transfer_amount=rule.min_transfer_amount,
                    max_transfer_amount=rule.max_transfer_amount,
                    exchange_rate=exchange_rate,
                    conversion_path=conversion_path
                )
                rule_details.append(rule_detail)
            else:
                logger.info(f"Rule {rule.id} excluded: converted amount {converted_amount} is outside transfer limits")

        except HTTPException as e:
            logger.warning(f"Conversion failed for rule {rule.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing rule {rule.id}: {str(e)}")

    if not rule_details:
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    return OptimizedTransferRuleResponse(
        send_country=CountryResponse.model_validate(rules[0].send_country),
        receive_country=CountryResponse.model_validate(rules[0].receive_country),
        original_currency=CurrencyResponse.model_validate(from_currency),
        rules=rule_details
    )
