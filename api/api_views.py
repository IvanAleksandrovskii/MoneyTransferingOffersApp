from typing import List, Union, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, inspect, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, aliased, selectinload

from core import logger
from core.models import db_helper, Currency, Country, ProviderExchangeRate, TransferRule, TransferProvider
from core.schemas import (
    ProviderResponse, TransferRuleRequest, TransferRuleResponse,
    CurrencyResponse, CountryResponse, ExchangeRateResponse,
    GenericObjectResponse, TransferRuleFullRequest
)

router = APIRouter()


async def get_object_by_id_or_name(session: AsyncSession, model, id_or_name: Union[UUID, str]):
    try:
        if isinstance(id_or_name, str):
            try:
                id_or_name = UUID(id_or_name)
                query = select(model).filter(model.id == id_or_name)
            except ValueError:
                if model == Currency:
                    query = select(model).filter(or_(model.name == id_or_name, model.abbreviation == id_or_name))
                elif hasattr(model, 'name'):
                    query = select(model).filter(model.name == id_or_name)
                else:
                    raise HTTPException(status_code=400, detail=f"Cannot search {model.__name__} by name")
        else:
            query = select(model).filter(model.id == id_or_name)

    except Exception as e:
        logger.error(f"Error in get_object_by_id_or_name: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input for {model.__name__}")

    if model == Country:
        query = query.options(joinedload(Country.local_currency))

    result = await session.execute(query)
    obj = result.unique().scalar_one_or_none()

    if obj:
        logger.info(f"Found {model.__name__}: {obj.name if hasattr(obj, 'name') else obj.id}")
    else:
        logger.warning(f"{model.__name__} not found for input: {id_or_name}")

    return obj


async def convert_currency(session: AsyncSession, amount: float, from_currency: Currency, to_currency: Currency,
                           provider: TransferProvider) -> float:
    logger.info(
        f"Converting {amount} from {from_currency.abbreviation} to {to_currency.abbreviation} using provider {provider.name}")

    exchange_rate = await session.execute(
        select(ProviderExchangeRate)
        .filter(
            ProviderExchangeRate.provider_id == provider.id,
            ProviderExchangeRate.from_currency_id == from_currency.id,
            ProviderExchangeRate.to_currency_id == to_currency.id
        )
    )
    rate = exchange_rate.scalar_one_or_none()

    if not rate:
        logger.warning(
            f"Exchange rate not found for {from_currency.abbreviation} to {to_currency.abbreviation} using provider {provider.name}")
        raise HTTPException(
            status_code=404,
            detail=f"Exchange rate not found for {from_currency.abbreviation} to {to_currency.abbreviation} using provider {provider.name}"
        )

    logger.info(f"Exchange rate found: {rate.rate}")
    return amount * rate.rate


@router.get("/providers", response_model=List[ProviderResponse])
async def get_providers(session: AsyncSession = Depends(db_helper.session_getter)):
    query = (
        select(TransferProvider)
        .filter(TransferProvider.is_active == True)
        .options(selectinload(TransferProvider.transfer_rules).selectinload(TransferRule.send_country))
        .options(selectinload(TransferProvider.transfer_rules).selectinload(TransferRule.receive_country))
        .options(selectinload(TransferProvider.transfer_rules).selectinload(TransferRule.transfer_currency))
    )
    result = await session.execute(query)
    providers = result.unique().scalars().all()

    return [ProviderResponse.model_validate(provider) for provider in providers]


@router.post("/transfer-rules-by-countries", response_model=List[List[Any]])
async def get_transfer_rules_by_countries(
    transfer: TransferRuleRequest,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    logger.info(f"Searching for transfer rules: from {transfer.send_country} to {transfer.receive_country}")

    # Get country objects
    send_country = await get_object_by_id_or_name(session, Country, transfer.send_country)
    receive_country = await get_object_by_id_or_name(session, Country, transfer.receive_country)

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


@router.post("/transfer-rules-full-filled-info", response_model=List[TransferRuleResponse])
async def get_transfer_rules_full_filled_info(
        transfer: TransferRuleFullRequest,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    # Get country objects
    send_country = await get_object_by_id_or_name(session, Country, transfer.send_country)
    receive_country = await get_object_by_id_or_name(session, Country, transfer.receive_country)
    if not send_country or not receive_country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Get currency object
    from_currency = await get_object_by_id_or_name(session, Currency, transfer.from_currency)
    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    logger.info(
        f"Searching for rules: from {send_country.name} to {receive_country.name}, amount: {transfer.amount} {from_currency.abbreviation}")

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

    valid_rules = []
    for rule in rules:
        logger.info(f"Checking rule {rule.id}: {rule.provider.name}, {rule.transfer_currency.abbreviation}")

        original_amount = transfer.amount
        converted_amount = original_amount
        conversion_path = []

        if rule.transfer_currency.id != from_currency.id:
            try:
                # Прямая конвертация
                converted_amount = await convert_currency(session, original_amount, from_currency,
                                                          rule.transfer_currency, rule.provider)
                conversion_path = [from_currency, rule.transfer_currency]
            except HTTPException:
                logger.info(f"Direct conversion not found, trying through USD")
                try:
                    # Конвертация через USD
                    usd_currency = await get_object_by_id_or_name(session, Currency, "USD")
                    amount_in_usd = await convert_currency(session, original_amount, from_currency, usd_currency,
                                                           rule.provider)
                    converted_amount = await convert_currency(session, amount_in_usd, usd_currency,
                                                              rule.transfer_currency, rule.provider)
                    conversion_path = [from_currency, usd_currency, rule.transfer_currency]
                except HTTPException as e:
                    logger.error(f"Error converting currency for rule {rule.id}: {str(e)}")
                    continue  # Пропускаем это правило, если конвертация не удалась

        logger.info(f"Converted amount: {converted_amount} {rule.transfer_currency.abbreviation}")
        logger.info(f"Conversion path: {' -> '.join([c.abbreviation for c in conversion_path])}")

        # Расчет комиссии за перевод
        transfer_fee = converted_amount * (rule.fee_percentage / 100)
        amount_received = converted_amount - transfer_fee

        if rule.min_transfer_amount <= converted_amount <= (rule.max_transfer_amount or float('inf')):
            valid_rule = TransferRuleResponse(
                id=rule.id,
                send_country=CountryResponse.model_validate(rule.send_country),
                receive_country=CountryResponse.model_validate(rule.receive_country),
                provider=ProviderResponse.model_validate(rule.provider),
                transfer_fee_percentage=rule.fee_percentage,
                min_transfer_amount=rule.min_transfer_amount,
                max_transfer_amount=rule.max_transfer_amount,
                transfer_method=rule.transfer_method,
                estimated_transfer_time=rule.estimated_transfer_time,
                required_documents=rule.required_documents,
                original_amount=original_amount,
                original_currency=CurrencyResponse.model_validate(from_currency),
                converted_amount=converted_amount,
                transfer_currency=CurrencyResponse.model_validate(rule.transfer_currency),
                transfer_fee=transfer_fee,
                amount_received=amount_received
            )
            valid_rules.append(valid_rule)
            logger.info(f"Rule {rule.id} is valid")
        else:
            logger.info(
                f"Rule {rule.id} is not valid. Amount {converted_amount} is out of range [{rule.min_transfer_amount}, {rule.max_transfer_amount or 'inf'}]")

    if not valid_rules:
        logger.warning("No valid rules found after applying amount restrictions")
        raise HTTPException(status_code=404, detail="No valid transfer rules found for the specified parameters")

    return valid_rules


@router.get("/provider/{provider_id}/exchange-rates", response_model=List[ExchangeRateResponse])
async def get_provider_exchange_rates(
        provider_id: Union[UUID, str],
        session: AsyncSession = Depends(db_helper.session_getter)
):
    provider = await get_object_by_id_or_name(session, TransferProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found with id or name: {provider_id}")

    query = (
        select(ProviderExchangeRate)
        .filter(ProviderExchangeRate.provider_id == provider.id)
        .options(
            joinedload(ProviderExchangeRate.provider),
            joinedload(ProviderExchangeRate.from_currency),
            joinedload(ProviderExchangeRate.to_currency)
        )
    )
    result = await session.execute(query)
    rates = result.unique().scalars().all()

    return [
        ExchangeRateResponse(
            id=rate.id,
            provider=ProviderResponse(
                id=provider.id,
                name=provider.name
            ),
            from_currency=CurrencyResponse.model_validate(rate.from_currency),
            to_currency=CurrencyResponse.model_validate(rate.to_currency),
            rate=rate.rate,
            last_updated=rate.last_updated
        )
        for rate in rates
    ]


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


@router.get("/currency/{id_or_name}", response_model=CurrencyResponse)
async def get_currency(
        id_or_name: Union[UUID, str],
        session: AsyncSession = Depends(db_helper.session_getter)
):
    currency = await get_object_by_id_or_name(session, Currency, id_or_name)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return CurrencyResponse.model_validate(currency)


@router.get("/country/{id_or_name}", response_model=CountryResponse)
async def get_country(
        id_or_name: Union[UUID, str],
        session: AsyncSession = Depends(db_helper.session_getter)
):
    country = await get_object_by_id_or_name(session, Country, id_or_name)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return CountryResponse.model_validate(country)


@router.get("/currencies", response_model=List[CurrencyResponse])
async def get_all_currencies(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(Currency)
    result = await session.execute(query)
    currencies = result.scalars().all()
    return [CurrencyResponse.model_validate(currency) for currency in currencies]


@router.get("/countries", response_model=List[CountryResponse])
async def get_all_countries(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(Country).options(joinedload(Country.local_currency))
    result = await session.execute(query)
    countries = result.unique().scalars().all()
    return [CountryResponse.model_validate(country) for country in countries]


@router.get("/exchange-rates", response_model=List[ExchangeRateResponse])
async def get_all_exchange_rates(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(ProviderExchangeRate).options(
        joinedload(ProviderExchangeRate.provider),
        joinedload(ProviderExchangeRate.from_currency),
        joinedload(ProviderExchangeRate.to_currency)
    )
    result = await session.execute(query)
    rates = result.scalars().all()
    return [ExchangeRateResponse.model_validate(rate) for rate in rates]


@router.get("/transfer-rules", response_model=List[List[Any]])
async def get_all_transfer_rules(session: AsyncSession = Depends(db_helper.session_getter)):
    query = select(TransferRule).options(
        joinedload(TransferRule.send_country),
        joinedload(TransferRule.receive_country),
        joinedload(TransferRule.provider),
        joinedload(TransferRule.transfer_currency)
    )
    result = await session.execute(query)
    rules = result.unique().scalars().all()

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
