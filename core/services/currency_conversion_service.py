from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from core import logger
from core.models import Currency, TransferProvider
from core.services.convert_currency import convert_currency
from core.services.get_currency_by_abbreviation import get_currency_by_abbreviation


class CurrencyConversionService:
    @staticmethod
    async def convert_amount(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float, float, list[str]]:
        original_amount = round(amount, 2)

        if to_currency.id == from_currency.id:
            logger.info(f"No conversion needed: {from_currency.abbreviation} to {to_currency.abbreviation}")
            return original_amount, 1.0, [from_currency.abbreviation]

        try:
            # Попытка прямой конвертации
            converted_amount, exchange_rate, conversion_path = await CurrencyConversionService._try_direct_conversion(
                session, original_amount, from_currency, to_currency, provider
            )
            return converted_amount, exchange_rate, conversion_path
        except HTTPException as e:
            if e.status_code != 404:
                raise
            logger.info(f"Direct conversion failed. Attempting USD conversion.")

        # Попытка конвертации через USD
        try:
            converted_amount, exchange_rate, conversion_path = await CurrencyConversionService._try_usd_conversion(
                session, original_amount, from_currency, to_currency, provider
            )
            return converted_amount, exchange_rate, conversion_path
        except HTTPException as e:
            logger.error(f"Both direct and USD conversion failed: {str(e)}")
            raise HTTPException(status_code=400, detail="Unable to perform currency conversion")

    @staticmethod
    async def _try_direct_conversion(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float, float, list[str]]:
        logger.info(f"Attempting direct conversion: {amount} {from_currency.abbreviation} to {to_currency.abbreviation}")
        converted_amount, rate = await convert_currency(session, amount, from_currency, to_currency, provider)
        converted_amount = round(converted_amount, 2)
        exchange_rate = round(rate, 4)
        conversion_path = [from_currency.abbreviation, to_currency.abbreviation]
        logger.info(f"Direct conversion successful: {amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
        return converted_amount, exchange_rate, conversion_path

    @staticmethod
    async def _try_usd_conversion(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float, float, list[str]]:
        logger.info(f"Attempting conversion through USD: {amount} {from_currency.abbreviation} to {to_currency.abbreviation}")
        usd_currency = await get_currency_by_abbreviation(session, "USD")
        if not usd_currency:
            raise HTTPException(status_code=404, detail="USD currency not found in the database")

        # Конвертация из исходной валюты в USD
        amount_in_usd, rate_to_usd = await convert_currency(session, amount, from_currency, usd_currency, provider)
        logger.info(f"Converted to USD: {amount_in_usd} USD")

        # Конвертация из USD в целевую валюту
        final_amount, rate_from_usd = await convert_currency(session, amount_in_usd, usd_currency, to_currency, provider)

        converted_amount = round(final_amount, 2)
        exchange_rate = round(rate_to_usd * rate_from_usd, 4)
        conversion_path = [from_currency.abbreviation, "USD", to_currency.abbreviation]
        logger.info(f"USD conversion successful: {amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
        return converted_amount, exchange_rate, conversion_path
