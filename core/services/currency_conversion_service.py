from async_lru import alru_cache
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from datetime import datetime, timedelta

from core import logger, settings
from core.models import Currency, TransferProvider, ProviderExchangeRate


class CurrencyConversionService:
    """
    Service for currency conversion, stores USD conversion rate in cache to avoid multiple queries and
    reduce the number of database queries. Loads cache memory at the same time.
    """
    @staticmethod
    async def convert_amount(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float, float, list[str]]:
        """
        Convert amount from one currency to another
        :param session: Async database session
        :param amount: Amount to convert
        :param from_currency: From currency object
        :param to_currency: To currency object
        :param provider: Transfer provider object
        :return: Converted amount, exchange rate, conversion path (list of currency abbreviations used in the conversion)
        """

        # Input validation
        if not amount:
            raise HTTPException(status_code=400, detail="Amount not provided")
        original_amount = round(amount, 2)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")
        if not from_currency or not to_currency:
            raise HTTPException(status_code=400, detail="Currency not provided")

        # Check if conversion is needed
        if to_currency.id == from_currency.id:
            logger.info(f"No conversion needed: {from_currency.abbreviation} to {to_currency.abbreviation}")
            return original_amount, 1.0, [from_currency.abbreviation]

        # Get USD currency, to avoid multiple queries result stores in cache
        usd_currency = await CurrencyConversionService._get_usd_currency(session)
        # Fetch all necessary exchange rates in a single query
        exchange_rates = await CurrencyConversionService._get_exchange_rates(
            session, provider.id, [from_currency.id, to_currency.id, usd_currency.id]
        )

        # Try direct conversion first
        direct_rate = exchange_rates.get((from_currency.id, to_currency.id))
        if direct_rate:
            converted_amount = round(original_amount * direct_rate, 2)
            exchange_rate = round(direct_rate, 4)
            conversion_path = [from_currency.abbreviation, to_currency.abbreviation]
            logger.info(f"Direct conversion successful: {original_amount} {from_currency.abbreviation} = "
                        f"{converted_amount} {to_currency.abbreviation}")
            return converted_amount, exchange_rate, conversion_path

        # If direct conversion is not available, try USD as an intermediate currency
        rate_to_usd = exchange_rates.get((from_currency.id, usd_currency.id))
        rate_from_usd = exchange_rates.get((usd_currency.id, to_currency.id))
        if rate_to_usd and rate_from_usd:
            amount_in_usd = original_amount * rate_to_usd
            converted_amount = round(amount_in_usd * rate_from_usd, 2)
            exchange_rate = round(rate_to_usd * rate_from_usd, 4)
            conversion_path = [from_currency.abbreviation, "USD", to_currency.abbreviation]
            logger.info(
                f"USD conversion successful: {original_amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
            return converted_amount, exchange_rate, conversion_path

        # If no conversion path is found, raise an exception
        logger.error(f"Unable to perform currency conversion from {from_currency.abbreviation} to {to_currency.abbreviation}")
        raise HTTPException(status_code=400, detail="Unable to perform currency conversion")

    @staticmethod
    @alru_cache(maxsize=1, ttl=settings.cache.usd_currency_cache_sec)  # To make it infinite just delete "ttl=..."
    async def _get_usd_currency(session: AsyncSession) -> Currency:
        try:
            usd_currency = await session.execute(Currency.active().filter(Currency.abbreviation == "USD"))
            usd_currency = usd_currency.scalar_one_or_none()
            if not usd_currency:
                raise HTTPException(status_code=404, detail="Active USD currency not found in the database")
            return usd_currency
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    async def _get_exchange_rates(session: AsyncSession, provider_id: str, currency_ids: list[str]) -> dict:
        """
        Fetch all relevant exchange rates in a single query
        :param session: Async database session
        :param provider_id: ID of the transfer provider
        :param currency_ids: List of currency IDs to fetch rates for
        :return: Dictionary of exchange rates
        """
        query = (
            ProviderExchangeRate.active()
            .filter(
                ProviderExchangeRate.provider_id == provider_id,
                ProviderExchangeRate.from_currency_id.in_(currency_ids),
                ProviderExchangeRate.to_currency_id.in_(currency_ids)
            )
        )
        try:
            result = await session.execute(query)
            rates = result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        return {(rate.from_currency_id, rate.to_currency_id): rate.rate for rate in rates}
