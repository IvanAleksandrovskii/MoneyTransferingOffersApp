from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferRule, ProviderExchangeRate
from core.schemas import (
    TransferRuleRequest, TransferRuleFullRequest, OptimizedTransferRuleResponse,
    TransferRuleDetails, DetailedTransferRuleResponse, CurrencyResponse, CountryResponse, ProviderResponse,
)
from core.services.convert_currency import convert_currency
from core.services.get_currency_by_abbreviation import get_currency_by_abbreviation
from core.services.get_object import get_object_by_id


router = APIRouter()


@router.post("/transfer-rules-by-countries", response_model=List[DetailedTransferRuleResponse])
async def get_transfer_rules_by_countries(
        transfer: TransferRuleRequest,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    logger.info(f"Searching for transfer rules: from {transfer.send_country} to {transfer.receive_country}")

    send_country = await get_object_by_id(session, Country, transfer.send_country)
    receive_country = await get_object_by_id(session, Country, transfer.receive_country)

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


@router.post("/transfer-rules-full-filled-info", response_model=OptimizedTransferRuleResponse)
async def get_transfer_rules_full_filled_info(
        transfer: TransferRuleFullRequest,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    send_country = await get_object_by_id(session, Country, transfer.send_country)
    receive_country = await get_object_by_id(session, Country, transfer.receive_country)
    if not send_country or not receive_country:
        raise HTTPException(status_code=404, detail="Country not found")

    from_currency = await get_object_by_id(session, Currency, transfer.from_currency)
    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    logger.info(f"Searching for rules: from {send_country.name} to {receive_country.name}, amount: {transfer.amount} {from_currency.abbreviation}")

    query = (
        select(TransferRule)
        .options(
            joinedload(TransferRule.send_country).joinedload(Country.local_currency),
            joinedload(TransferRule.receive_country).joinedload(Country.local_currency),
            joinedload(TransferRule.provider),
            joinedload(TransferRule.transfer_currency)
        )
        .filter(
            TransferRule.send_country_id == send_country.id,
            TransferRule.receive_country_id == receive_country.id
        )
    )

    result = await session.execute(query)
    rules = result.unique().scalars().all()

    if not rules:
        logger.warning("No transfer rules found for the specified countries")
        raise HTTPException(status_code=404, detail="No transfer rules found for the specified countries")

    rule_details = []
    for rule in rules:
        try:
            logger.info(f"Checking rule {rule.id}: {rule.provider.name}, {rule.transfer_currency.abbreviation}")

            original_amount = round(transfer.amount, 2)  # Round the input amount to 2 decimal places
            converted_amount = original_amount
            exchange_rate = 1.0  # Default exchange rate to 1.0 if no conversion is needed
            conversion_path = []

            if rule.transfer_currency.id != from_currency.id:
                try:
                    exchange_rate_query = select(ProviderExchangeRate).filter(
                        ProviderExchangeRate.provider_id == rule.provider_id,
                        ProviderExchangeRate.from_currency_id == from_currency.id,
                        ProviderExchangeRate.to_currency_id == rule.transfer_currency_id
                    )
                    exchange_rate_result = await session.execute(exchange_rate_query)
                    exchange_rate_obj = exchange_rate_result.scalar_one_or_none()

                    if exchange_rate_obj:
                        exchange_rate = exchange_rate_obj.rate
                        converted_amount = round(original_amount * exchange_rate,
                                                 2)  # Round the converted amount to 2 decimal places
                        conversion_path = [from_currency.abbreviation, rule.transfer_currency.abbreviation]
                    else:
                        logger.info(f"Direct conversion not found, trying through USD")
                        usd_currency = await get_currency_by_abbreviation(session, "USD")
                        amount_in_usd = await convert_currency(session, original_amount, from_currency, usd_currency,
                                                               rule.provider)
                        converted_amount = await convert_currency(session, amount_in_usd, usd_currency,
                                                                  rule.transfer_currency, rule.provider)
                        converted_amount = round(converted_amount, 2)  # Round the converted amount to 2 decimal places
                        conversion_path = [from_currency.abbreviation, "USD", rule.transfer_currency.abbreviation]
                        exchange_rate = round(converted_amount / original_amount,
                                              3)  # Round the exchange rate to 3 decimal places
                except Exception as e:
                    logger.error(f"Error converting currency for rule {rule.id}: {str(e)}")
                    continue
            else:
                logger.info(f"No conversion needed. Original currency matches transfer currency.")
                conversion_path = [from_currency.abbreviation]

            logger.info(f"Converted amount: {converted_amount} {rule.transfer_currency.abbreviation}")
            logger.info(f"Exchange rate: {exchange_rate}")
            logger.info(f"Conversion path: {' -> '.join(conversion_path)}")

            fee_percentage = rule.fee_percentage / 100
            transfer_fee = round(converted_amount * fee_percentage, 2)  # Round the transfer fee to 2 decimal places
            amount_received = round(converted_amount - transfer_fee, 2)  # Round the amount received to 2 decimal places

            if rule.min_transfer_amount <= converted_amount <= (rule.max_transfer_amount or float('inf')):
                rule_detail = TransferRuleDetails(
                    id=rule.id,
                    provider=ProviderResponse(id=rule.provider.id, name=rule.provider.name, url=rule.provider.url),
                    transfer_method=rule.transfer_method,
                    estimated_transfer_time=rule.estimated_transfer_time,
                    required_documents=rule.required_documents,
                    original_amount=original_amount,
                    converted_amount=converted_amount,
                    transfer_currency=CurrencyResponse(
                        id=rule.transfer_currency.id,
                        name=rule.transfer_currency.name,
                        symbol=rule.transfer_currency.symbol,
                        abbreviation=rule.transfer_currency.abbreviation
                    ),
                    amount_received=amount_received,
                    transfer_fee=transfer_fee,
                    transfer_fee_percentage=rule.fee_percentage,
                    min_transfer_amount=rule.min_transfer_amount,
                    max_transfer_amount=rule.max_transfer_amount,
                    exchange_rate=exchange_rate,
                    conversion_path=conversion_path
                )
                rule_details.append(rule_detail)
                logger.info(f"Rule {rule.id} is valid")
            else:
                logger.info(
                    f"Rule {rule.id} is not valid. Amount {converted_amount} is out of range "
                    f"[{rule.min_transfer_amount}, {rule.max_transfer_amount or 'inf'}]"
                )
        except Exception as e:
            logger.error(f"Error processing rule {rule.id}: {str(e)}")
            continue

    if not rule_details:
        logger.warning("No valid rules found after applying amount restrictions")
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    return OptimizedTransferRuleResponse(
        send_country=CountryResponse(
            id=send_country.id,
            name=send_country.name,
            local_currency=CurrencyResponse(
                id=send_country.local_currency.id,
                name=send_country.local_currency.name,
                symbol=send_country.local_currency.symbol,
                abbreviation=send_country.local_currency.abbreviation
            )
        ),
        receive_country=CountryResponse(
            id=receive_country.id,
            name=receive_country.name,
            local_currency=CurrencyResponse(
                id=receive_country.local_currency.id,
                name=receive_country.local_currency.name,
                symbol=receive_country.local_currency.symbol,
                abbreviation=receive_country.local_currency.abbreviation
            )
        ),
        original_currency=CurrencyResponse(
            id=from_currency.id,
            name=from_currency.name,
            symbol=from_currency.symbol,
            abbreviation=from_currency.abbreviation
        ),
        rules=rule_details
    )
