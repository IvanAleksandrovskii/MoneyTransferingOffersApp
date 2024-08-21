from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferRule, TransferProvider, Document
from core.schemas import (
    OptimizedTransferRuleResponse, TransferRuleDetails,
    CurrencyResponse, CountryResponse, ProviderResponse,
    DocumentResponse, TimeDeltaInfo,
)
from core.services import CurrencyConversionService
from core.services import get_object_by_id
from utils import Ordering

router = APIRouter()

transfer_rule_ordering = Ordering(TransferRule, [
    "id", "fee_percentage", "min_transfer_amount", "max_transfer_amount",
    "transfer_method", "min_transfer_time", "max_transfer_time"
], default_field="fee_percentage")  # default_field to "fee_percentage"


@router.get("/transfer-rules-filtered", response_model=OptimizedTransferRuleResponse)
async def get_transfer_rules(
    send_country_id: UUID = Query(..., description="ID of the sending country"),
    receive_country_id: UUID = Query(..., description="ID of the receiving country"),
    optional_from_currency_id: Optional[UUID] = Query(None, description="ID of the sending currency"),
    optional_amount: Optional[float] = Query(None, description="Amount to transfer", gt=0),
    order: Optional[str] = Query(None, description="Field to order by"),
    order_desc: bool = Query(False, description="Order descending"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    """
    Get filtered transfer rules based on sending and receiving countries, optional currency and amount.
    """
    if not send_country_id or not receive_country_id:
        raise HTTPException(status_code=400, detail="Send country and receive country are required")

    logger.info(f"Searching for transfer rules: from {send_country_id} to {receive_country_id}")

    # Construct the base query with all necessary joins
    query = (
        TransferRule.active()
        .filter(
            TransferRule.send_country_id == send_country_id,
            TransferRule.receive_country_id == receive_country_id,
            TransferRule.provider.has(TransferProvider.is_active == True),
            TransferRule.send_country.has(Country.is_active == True),
            TransferRule.receive_country.has(Country.is_active == True),
            TransferRule.transfer_currency.has(Currency.is_active == True)
        )
        .options(
            joinedload(TransferRule.send_country).joinedload(Country.local_currency.and_(Currency.is_active == True)),
            joinedload(TransferRule.receive_country).joinedload(Country.local_currency.and_(Currency.is_active == True)),
            joinedload(TransferRule.provider.and_(TransferProvider.is_active == True)),
            joinedload(TransferRule.transfer_currency.and_(Currency.is_active == True)),
            joinedload(TransferRule.required_documents.and_(Document.is_active == True))
        )
        .order_by(transfer_rule_ordering.order_by(order, order_desc))
    )
    try:
        result = await session.execute(query)
        rules = result.unique().scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get transfer rules: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get transfer rules")

    if not rules:
        logger.warning(f"No active transfer rules found for countries: from {send_country_id} to {receive_country_id}")
        raise HTTPException(status_code=404, detail="No active transfer rules found for the specified countries")

    logger.info(f"Found {len(rules)} transfer rules")

    from_currency = None
    rule_details = []

    for rule in rules:
        try:
            logger.info(f"Processing rule {rule.id}")
            logger.info(f"min_transfer_time: {rule.min_transfer_time}, max_transfer_time: {rule.max_transfer_time}")

            # Process optional currency and amount if provided
            if optional_from_currency_id is not None:
                if from_currency is None:
                    from_currency = await get_object_by_id(session, Currency, optional_from_currency_id)
                    if not from_currency:
                        logger.warning(f"From currency not found: {optional_from_currency_id}")
                        continue  # Skip this rule, go to the next one
                    if not from_currency.is_active:
                        logger.warning(f"From currency is inactive: {from_currency.id}")
                        raise HTTPException(status_code=404, detail="From currency is inactive")

                if optional_amount is not None:
                    # Perform currency conversion
                    converted_amount, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                        session=session,
                        amount=optional_amount,
                        from_currency=from_currency,
                        to_currency=rule.transfer_currency,
                        provider=rule.provider
                    )

                    # Check if the converted amount is within the transfer limits
                    if rule.min_transfer_amount <= converted_amount <= rule.max_transfer_amount:
                        fee_percentage = rule.fee_percentage / 100
                        transfer_fee = round(converted_amount * fee_percentage, 2)
                        amount_received = round(converted_amount - transfer_fee, 2)
                    else:
                        logger.info(f"Rule {rule.id} excluded: converted amount {converted_amount} is outside transfer limits")
                        continue  # If the query amount is not in the transfer limits, go to the next rule
                else:
                    # Have currency but no amount, use dummy amount for exchange rate calculation
                    dummy_amount = 100
                    _, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                        session=session,
                        amount=dummy_amount,
                        from_currency=from_currency,
                        to_currency=rule.transfer_currency,
                        provider=rule.provider
                    )
                    converted_amount = None
                    amount_received = None
                    transfer_fee = None
            else:
                # No currency conversion needed
                converted_amount = None
                amount_received = None
                transfer_fee = None
                exchange_rate = None
                conversion_path = [rule.transfer_currency.abbreviation]

            # Construct TransferRuleDetails object
            rule_detail = TransferRuleDetails(
                id=rule.id,
                provider=ProviderResponse.model_validate(rule.provider),
                min_transfer_time=TimeDeltaInfo(
                    days=rule.min_transfer_time.days,
                    hours=rule.min_transfer_time.seconds // 3600,
                    minutes=(rule.min_transfer_time.seconds % 3600) // 60
                ),
                max_transfer_time=TimeDeltaInfo(
                    days=rule.max_transfer_time.days,
                    hours=rule.max_transfer_time.seconds // 3600,
                    minutes=(rule.max_transfer_time.seconds % 3600) // 60
                ),
                transfer_method=rule.transfer_method,
                required_documents=[DocumentResponse(id=doc.id, name=doc.name) for doc in rule.required_documents],
                original_amount=optional_amount,
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
            logger.info(f"Successfully processed rule {rule.id}")

        except HTTPException as e:
            logger.warning(f"Conversion failed for rule {rule.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing rule {rule.id}: {str(e)}", exc_info=True)

    if not rule_details:
        logger.warning("No valid transfer rules found for the specified parameters")
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    logger.info(f"Returning {len(rule_details)} transfer rules")

    # Construct and return the final response
    return OptimizedTransferRuleResponse(
        send_country=CountryResponse.model_validate(rules[0].send_country),
        receive_country=CountryResponse.model_validate(rules[0].receive_country),
        original_currency=CurrencyResponse.model_validate(from_currency) if from_currency else None,
        rules=rule_details
    )
