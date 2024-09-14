import asyncio
from typing import Optional, Dict, List, Tuple
from uuid import UUID

from async_lru import alru_cache
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from core import logger, settings
from core.models import db_helper, Currency, Country, TransferRule, TransferProvider
from core.schemas import (
    OptimizedTransferRuleResponse, TransferRuleDetails,
    CurrencyResponse, CountryResponse, ProviderResponse,
    DocumentResponse, TimeDeltaInfo,
)
from core.services import CurrencyConversionService
from utils import Ordering


router = APIRouter()

transfer_rule_ordering = Ordering(TransferRule, [
    "id", "fee_percentage", "min_transfer_amount", "max_transfer_amount",
    "transfer_method", "min_transfer_time", "max_transfer_time"
], default_field="fee_percentage")


def group_rules_by_provider(rules: List[TransferRule]) -> Dict[UUID, List[TransferRule]]:
    provider_rules = {}
    for rule in rules:
        if rule.provider_id not in provider_rules:
            provider_rules[rule.provider_id] = []
        provider_rules[rule.provider_id].append(rule)
    return provider_rules


async def process_rules(
        session: AsyncSession,
        provider_rules: Dict[UUID, List[TransferRule]],
        from_currency: Optional[Currency],
        optional_amount: Optional[float]
) -> List[TransferRuleDetails]:

    rule_details = []

    for provider_id, rules in provider_rules.items():
        best_rule = await select_best_rule(
            session, rules,
            from_currency.id if from_currency else None,
            optional_amount
        )

        if best_rule:
            rule_details.append(best_rule)

    return rule_details


@alru_cache(maxsize=1, ttl=settings.cache.usd_currency_cache_sec)
async def get_usd_currency(session: AsyncSession) -> Currency:
    usd_currency = await session.execute(Currency.active().filter(Currency.abbreviation == "USD"))
    usd_currency = usd_currency.scalar_one_or_none()
    if not usd_currency:
        raise HTTPException(status_code=404, detail="USD currency not found")
    return usd_currency


async def process_rule(session: AsyncSession, rule: TransferRule, from_currency: Optional[Currency],
                       optional_amount: Optional[float]) -> Optional[TransferRuleDetails]:
    try:
        converted_amount = None
        amount_received = None
        transfer_fee = None
        exchange_rate = None
        calculated_fee_percentage = rule.fee_percentage
        conversion_path = [rule.transfer_currency.abbreviation]

        if optional_amount is not None:
            if from_currency and from_currency.id != rule.transfer_currency.id:
                try:
                    converted_amount, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                        session=session,
                        amount=optional_amount,
                        from_currency=from_currency,
                        to_currency=rule.transfer_currency,
                        provider=rule.provider
                    )
                except HTTPException as e:
                    if e.status_code == 400 and e.detail == "Unable to perform currency conversion":
                        logger.info(f"Skipping rule {rule.id}: Unable to perform currency conversion")
                        return None
                    raise
            else:
                converted_amount = optional_amount
                exchange_rate = 1.0

            if rule.fee_fixed is not None and rule.fee_percentage == 0:
                transfer_fee = rule.fee_fixed
                calculated_fee_percentage = (transfer_fee / converted_amount) * 100
            else:
                fee_percentage = rule.fee_percentage / 100
                transfer_fee = round(converted_amount * fee_percentage, 2)
                calculated_fee_percentage = rule.fee_percentage

            amount_received = round(converted_amount - transfer_fee, 2)
            calculated_fee_percentage = round(calculated_fee_percentage, 2)

        elif from_currency and from_currency.id != rule.transfer_currency.id:
            dummy_amount = 100
            try:
                _, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                    session=session,
                    amount=dummy_amount,
                    from_currency=from_currency,
                    to_currency=rule.transfer_currency,
                    provider=rule.provider
                )
            except HTTPException as e:
                if e.status_code == 400 and e.detail == "Unable to perform currency conversion":
                    logger.info(f"Skipping rule {rule.id}: Unable to perform currency conversion")
                    return None
                raise

        return TransferRuleDetails(
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
            transfer_fee_percentage=calculated_fee_percentage,
            min_transfer_amount=rule.min_transfer_amount,
            max_transfer_amount=rule.max_transfer_amount,
            exchange_rate=exchange_rate,
            conversion_path=conversion_path
        )

    except Exception as e:
        logger.error(f"Error processing rule {rule.id}: {str(e)}", exc_info=True)
        return None


@alru_cache(maxsize=settings.cache.objects_cached_max_count, ttl=settings.cache.objects_cache_sec)
async def get_cached_currency(session: AsyncSession, currency_id: UUID) -> Optional[Currency]:
    if currency_id is None:
        return None
    currency = await session.get(Currency, currency_id)
    if currency and currency.is_active:
        return currency
    return None


async def select_best_rule(
        session: AsyncSession,
        rules: List[TransferRule],
        from_currency_id: Optional[UUID],
        optional_amount: Optional[float]
) -> Optional[TransferRuleDetails]:

    logger.info(f"Selecting best rule from {len(rules)} rules")

    async def process_and_rank_rule(rule: TransferRule) -> Tuple[Optional[TransferRuleDetails], int]:
        from_currency = await get_cached_currency(session, from_currency_id)

        result = await process_rule(session, rule, from_currency, optional_amount)
        if result:
            # Check if the converted amount is within the rule's limits
            if optional_amount is not None:
                if result.converted_amount < rule.min_transfer_amount:
                    logger.info(f"Rule {rule.id} skipped: amount {result.converted_amount} is less than minimum {rule.min_transfer_amount}")
                    return None, 3
                if rule.max_transfer_amount is not None and result.converted_amount > rule.max_transfer_amount:
                    logger.info(f"Rule {rule.id} skipped: amount {result.converted_amount} is greater than maximum {rule.max_transfer_amount}")
                    return None, 3

            # Rank: 1 for single currency path, 2 for multi-currency path
            rank = 1 if len(result.conversion_path) == 1 else 2
            return result, rank
        return None, 3  # Use 3 as a rank for invalid rules

    # Process all rules and sort them
    processed_rules = await asyncio.gather(*[process_and_rank_rule(rule) for rule in rules])
    valid_rules = [(rule, rank) for rule, rank in processed_rules if rule is not None]

    # Sort by rank (single currency first) and then by fee percentage
    sorted_rules = sorted(valid_rules, key=lambda x: (x[1], x[0].transfer_fee_percentage))

    if sorted_rules:
        best_rule, _ = sorted_rules[0]
        logger.info(f"Selected rule: {best_rule.id}")
        return best_rule

    logger.warning("No suitable rule found")
    return None


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

    try:
        # Fetch all relevant data in a single query
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
                joinedload(TransferRule.send_country).joinedload(Country.local_currency),
                joinedload(TransferRule.receive_country).joinedload(Country.local_currency),
                joinedload(TransferRule.provider),
                joinedload(TransferRule.transfer_currency),
                selectinload(TransferRule.required_documents)
            )
            .order_by(transfer_rule_ordering.order_by(order, order_desc))
        )

        result = await session.execute(query)
        rules = list(result.unique().scalars().all())

        if not rules:
            logger.warning(
                f"No active transfer rules found for countries: from {send_country_id} to {receive_country_id}")
            raise HTTPException(status_code=404, detail="No active transfer rules found for the specified countries")

        logger.info(f"Found {len(rules)} transfer rules")

        send_country = rules[0].send_country
        receive_country = rules[0].receive_country

        from_currency = None
        if optional_from_currency_id:
            from_currency = await session.get(Currency, optional_from_currency_id)
            if not from_currency or not from_currency.is_active:
                raise HTTPException(status_code=404, detail="From currency not found or inactive")

        # Group rules by provider
        provider_rules = group_rules_by_provider(rules)

        # Process rules
        rule_details = await process_rules(session, provider_rules, from_currency, optional_amount)

        if not rule_details:
            logger.warning("No valid transfer rules found for the specified parameters")
            raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

        # Sort rule_details if amount is provided
        if optional_amount is not None:
            def calculate_fee_percentage(rule):
                if rule.converted_amount and rule.amount_received and rule.converted_amount > 0:
                    fee = rule.converted_amount - rule.amount_received
                    return (fee / rule.converted_amount) * 100
                return float('inf')  # Nothing can be more than 'inf'

            # Filter out rules with negative converted_amount
            rule_details = [rule for rule in rule_details if
                            rule.converted_amount is None or rule.converted_amount >= 0]

            rule_details.sort(key=calculate_fee_percentage)

        logger.info(f"Returning {len(rule_details)} transfer rules")

        # Construct and return the final response
        return OptimizedTransferRuleResponse(
            send_country=CountryResponse.model_validate(send_country),
            receive_country=CountryResponse.model_validate(receive_country),
            original_currency=CurrencyResponse.model_validate(from_currency) if from_currency else None,
            rules=rule_details
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
