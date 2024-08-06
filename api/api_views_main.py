from typing import List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, ProviderExchangeRate, TransferRule, TransferProvider
from core.schemas import (
    ProviderResponse, TransferRuleRequest,
    CurrencyResponse, CountryResponse, GenericObjectResponse, TransferRuleFullRequest, OptimizedTransferRuleResponse, TransferRuleDetails
)
from core.services.convert_currency import convert_currency
from core.services.get_currency_by_abbreviation import get_currency_by_abbreviation
from core.services.get_object import get_object_by_id

router = APIRouter()


@router.post("/transfer-rules-by-countries", response_model=List[List[Any]])
async def get_transfer_rules_by_countries(
    transfer: TransferRuleRequest,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    logger.info(f"Searching for transfer rules: from {transfer.send_country} to {transfer.receive_country}")

    # Get country objects
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

    return [
        [
            rule.provider.name if rule.provider else "Unknown",
            rule.send_country.name if rule.send_country else "Unknown",
            rule.receive_country.name if rule.receive_country else "Unknown",
            rule.transfer_currency.abbreviation if rule.transfer_currency else "Unknown",
            rule.min_transfer_amount,
            rule.max_transfer_amount
        ]
        for rule in rules
    ]


@router.post("/transfer-rules-full-filled-info", response_model=OptimizedTransferRuleResponse)
async def get_transfer_rules_full_filled_info(
        transfer: TransferRuleFullRequest,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    # Get country objects
    send_country = await get_object_by_id(session, Country, transfer.send_country)
    receive_country = await get_object_by_id(session, Country, transfer.receive_country)
    if not send_country or not receive_country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Get currency object
    from_currency = await get_object_by_id(session, Currency, transfer.from_currency)
    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    logger.info(
        f"Searching for rules: from {send_country.name} to {receive_country.name}, amount: {transfer.amount} "
        f"{from_currency.abbreviation}")

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
        logger.info(f"Checking rule {rule.id}: {rule.provider.name}, {rule.transfer_currency.abbreviation}")

        original_amount = transfer.amount
        converted_amount = original_amount
        conversion_path = []

        if rule.transfer_currency.id != from_currency.id:
            try:
                # Straight conversion
                converted_amount = await convert_currency(session, original_amount, from_currency,
                                                          rule.transfer_currency, rule.provider)
                conversion_path = [from_currency, rule.transfer_currency]
            except HTTPException:
                logger.info(f"Direct conversion not found, trying through USD")
                try:
                    # Convert with USD
                    usd_currency = await get_currency_by_abbreviation(session, "USD")
                    amount_in_usd = await convert_currency(session, original_amount, from_currency, usd_currency,
                                                           rule.provider)
                    converted_amount = await convert_currency(session, amount_in_usd, usd_currency,
                                                              rule.transfer_currency, rule.provider)
                    conversion_path = [from_currency, usd_currency, rule.transfer_currency]
                except HTTPException as e:
                    logger.error(f"Error converting currency for rule {rule.id}: {str(e)}")
                    continue  # Skip this rule if conversion fails

        logger.info(f"Converted amount: {converted_amount} {rule.transfer_currency.abbreviation}")
        logger.info(f"Conversion path: {' -> '.join([c.abbreviation for c in conversion_path])}")

        # Calculate transfer fee
        transfer_fee = converted_amount * (rule.fee_percentage / 100)
        amount_received = converted_amount - transfer_fee

        if rule.min_transfer_amount <= converted_amount <= (rule.max_transfer_amount or float('inf')):
            rule_detail = TransferRuleDetails(
                id=rule.id,
                provider=ProviderResponse.model_validate(rule.provider),
                transfer_method=rule.transfer_method,
                estimated_transfer_time=rule.estimated_transfer_time,
                required_documents=rule.required_documents,
                original_amount=original_amount,
                converted_amount=converted_amount,
                transfer_currency=CurrencyResponse.model_validate(rule.transfer_currency),
                transfer_fee=transfer_fee,
                amount_received=amount_received,
                transfer_fee_percentage=rule.fee_percentage,
                min_transfer_amount=rule.min_transfer_amount,
                max_transfer_amount=rule.max_transfer_amount
            )
            rule_details.append(rule_detail)
            logger.info(f"Rule {rule.id} is valid")
        else:
            logger.info(
                f"Rule {rule.id} is not valid. Amount {converted_amount} is out of range [{rule.min_transfer_amount}, {rule.max_transfer_amount or 'inf'}]")

    if not rule_details:
        logger.warning("No valid rules found after applying amount restrictions")
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    return OptimizedTransferRuleResponse(
        send_country=CountryResponse.model_validate(send_country),
        receive_country=CountryResponse.model_validate(receive_country),
        original_currency=CurrencyResponse.model_validate(from_currency),
        rules=rule_details
    )


# TODO: SUPER ENDPOINT - del (?)
@router.get("/object/{uuid}", response_model=GenericObjectResponse)
async def get_object_by_uuid(
        uuid: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    for model in [Country, Currency, TransferProvider, TransferRule, ProviderExchangeRate]:
        obj = await session.get(model, uuid)
        if obj:
            # Extract data excluding SQLAlchemy fields
            data = {
                attr_name: getattr(obj, attr_name)
                for attr_name, column in inspect(model).mapper.column_attrs.items()
                if not attr_name.startswith('_')
            }
            return GenericObjectResponse(
                object_type=model.__name__,
                data=data
            )
    raise HTTPException(status_code=404, detail="Object not found")
