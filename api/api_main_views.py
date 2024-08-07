from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferRule
from core.schemas import (
    TransferRuleRequest, TransferRuleFullRequest, OptimizedTransferRuleResponse,
    TransferRuleDetails, DetailedTransferRuleResponse, CurrencyResponse, CountryResponse,
    ProviderResponse,
)
from core.services import CurrencyConversionService
from core.services import get_object_by_id


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
    # Retrieve send and receive countries
    send_country = await get_object_by_id(session, Country, transfer.send_country)
    receive_country = await get_object_by_id(session, Country, transfer.receive_country)
    if not send_country or not receive_country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Retrieve the source currency
    from_currency = await get_object_by_id(session, Currency, transfer.from_currency)
    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    logger.info(f"Searching for rules: from {send_country.name} to {receive_country.name}, amount: {transfer.amount} {from_currency.abbreviation}")

    # Construct query to fetch transfer rules
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

    # Execute query and fetch results
    result = await session.execute(query)
    rules = result.unique().scalars().all()

    if not rules:
        logger.warning("No transfer rules found for the specified countries")
        raise HTTPException(status_code=404, detail="No transfer rules found for the specified countries")

    rule_details = []
    for rule in rules:
        try:
            logger.info(f"Checking rule {rule.id}: {rule.provider.name}, {rule.transfer_currency.abbreviation}")

            # Perform currency conversion
            original_amount = transfer.amount
            converted_amount, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                session, original_amount, from_currency, rule.transfer_currency, rule.provider
            )

            logger.info(f"Converted amount: {converted_amount} {rule.transfer_currency.abbreviation}")
            logger.info(f"Exchange rate: {exchange_rate}")
            logger.info(f"Conversion path: {' -> '.join(conversion_path)}")

            # Calculate fees and final amount
            fee_percentage = rule.fee_percentage / 100
            transfer_fee = round(converted_amount * fee_percentage, 2)
            amount_received = round(converted_amount - transfer_fee, 2)

            # Check if the converted amount is within the allowed range
            if rule.min_transfer_amount <= converted_amount <= (rule.max_transfer_amount or float('inf')):
                # Create TransferRuleDetails object
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
        except HTTPException as e:
            if e.status_code == 400:  # This is the status code we set for failed conversions
                logger.warning(f"Conversion failed for rule {rule.id}: {str(e)}")
            else:
                logger.error(f"Error processing rule {rule.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing rule {rule.id}: {str(e)}")

    if not rule_details:
        logger.warning("No valid rules found after applying amount restrictions")
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    # Construct and return the response
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
