from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, TransferProvider, ProviderExchangeRate, TransferRule
from core.schemas import (
    CurrencyResponse, CountryResponse,
    ExchangeRateResponse, ProviderResponse, TransferRuleDetails,
    OptimizedTransferRuleResponse
)
from core.services import get_object_by_name, CurrencyConversionService

router = APIRouter()


# TODO: WARNING: (!) THIS IS VERY HIGH LOAD VIEWS (!)
# TODO: Make the same with abbreviations (?)
@router.get("/transfer-rules-by-countries", response_model=OptimizedTransferRuleResponse)
async def get_transfer_rules_by_countries(
    send_country: str = Query(..., min_length=1, description="Name of the sending country"),
    receive_country: str = Query(..., min_length=1, description="Name of the receiving country"),
    from_currency: Optional[str] = Query(None, description="Name of the sending currency"),
    amount: Optional[float] = Query(None, description="Amount to transfer", gt=0),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    if not send_country or not receive_country:
        raise HTTPException(status_code=400, detail="Send country and receive country are required")

    logger.info(f"Searching for transfer rules: from {send_country} to {receive_country}")

    # First, get the country IDs
    country_query = select(Country.id).where(
        or_(
            Country.name.ilike(f"%{send_country}%"),
            Country.name.ilike(f"%{receive_country}%")
        )
    )
    country_result = await session.execute(country_query)
    country_ids = country_result.scalars().all()

    if len(country_ids) < 2:
        raise HTTPException(status_code=404, detail="One or both countries not found")

    # Now, use these IDs to query the transfer rules
    query = (
        select(TransferRule)
        .filter(
            TransferRule.send_country_id.in_(country_ids),
            TransferRule.receive_country_id.in_(country_ids)
        )
        .options(
            joinedload(TransferRule.send_country).joinedload(Country.local_currency),
            joinedload(TransferRule.receive_country).joinedload(Country.local_currency),
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

    from_currency_obj = None
    if from_currency:
        from_currency_obj = await get_object_by_name(session, Currency, from_currency)
        if not from_currency_obj:
            raise HTTPException(status_code=404, detail="From currency not found")

    rule_details = []
    for rule in rules:
        try:
            if from_currency_obj:
                if amount is not None:
                    converted_amount, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                        session=session,
                        amount=amount,
                        from_currency=from_currency_obj,
                        to_currency=rule.transfer_currency,
                        provider=rule.provider
                    )

                    if rule.min_transfer_amount <= converted_amount <= rule.max_transfer_amount:
                        fee_percentage = rule.fee_percentage / 100
                        transfer_fee = round(converted_amount * fee_percentage, 2)
                        amount_received = round(converted_amount - transfer_fee, 2)
                    else:
                        logger.info(f"Rule {rule.id} excluded: converted amount {converted_amount} is outside transfer limits")
                        continue
                else:
                    # Have currency but no amount
                    dummy_amount = 100  # Use dummy amount to calculate conversion
                    _, exchange_rate, conversion_path = await CurrencyConversionService.convert_amount(
                        session=session,
                        amount=dummy_amount,
                        from_currency=from_currency_obj,
                        to_currency=rule.transfer_currency,
                        provider=rule.provider
                    )
                    converted_amount = amount_received = transfer_fee = None
            else:
                converted_amount = amount_received = transfer_fee = exchange_rate = None
                conversion_path = [rule.transfer_currency.abbreviation]

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

        except HTTPException as e:
            logger.warning(f"Conversion failed for rule {rule.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing rule {rule.id}: {str(e)}")

    if not rule_details:
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    return OptimizedTransferRuleResponse(
        send_country=CountryResponse.model_validate(rules[0].send_country),
        receive_country=CountryResponse.model_validate(rules[0].receive_country),
        original_currency=CurrencyResponse.model_validate(from_currency_obj) if from_currency_obj else None,
        rules=rule_details
    )


@router.get("/provider/rules", response_model=ProviderResponse)
async def get_provider_rules_by_name(
    provider_name: str = Query(..., min_length=1, description="Name of the provider"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = (
        select(TransferProvider)
        .filter(TransferProvider.name.ilike(f"%{provider_name}%"))
        .options(joinedload(TransferProvider.transfer_rules))
    )
    result = await session.execute(query)
    provider = result.unique().scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return ProviderResponse.model_validate(provider)


@router.get("/provider/exchange-rates", response_model=list[ExchangeRateResponse])
async def get_provider_exchange_rates_by_name(
    provider_name: str = Query(..., min_length=1, description="Name of the provider"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = (
        select(ProviderExchangeRate)
        .join(ProviderExchangeRate.provider)
        .filter(TransferProvider.name.ilike(f"%{provider_name}%"))
        .options(
            joinedload(ProviderExchangeRate.provider),
            joinedload(ProviderExchangeRate.from_currency),
            joinedload(ProviderExchangeRate.to_currency)
        )
    )
    result = await session.execute(query)
    rates = result.unique().scalars().all()

    if not rates:
        raise HTTPException(status_code=404, detail="No exchange rates found for the specified provider")

    return [ExchangeRateResponse.model_validate(rate) for rate in rates]


@router.get("/currency", response_model=CurrencyResponse)
async def get_currency_by_name(
    currency_name: str = Query(..., min_length=1, description="Name of the currency"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Currency).filter(Currency.name.ilike(f"%{currency_name}%"))
    result = await session.execute(query)
    currency = result.scalar_one_or_none()

    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    return CurrencyResponse.model_validate(currency)


@router.get("/country", response_model=CountryResponse)
async def get_country_by_name(
    country_name: str = Query(..., min_length=1, description="Name of the country"),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = (
        select(Country)
        .filter(Country.name.ilike(f"%{country_name}%"))
        .options(joinedload(Country.local_currency))
    )
    result = await session.execute(query)
    country = result.unique().scalar_one_or_none()

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    return CountryResponse.model_validate(country)
