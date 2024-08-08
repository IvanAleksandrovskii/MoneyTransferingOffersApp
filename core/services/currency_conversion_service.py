from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from core import logger
from core.models import Currency, TransferProvider
from core.services import convert_currency, get_currency_by_abbreviation


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

        converted_amount, exchange_rate, conversion_path = await CurrencyConversionService._try_direct_conversion(
            session, original_amount, from_currency, to_currency, provider
        )

        if converted_amount is None:
            converted_amount, exchange_rate, conversion_path = await CurrencyConversionService._try_usd_conversion(
                session, original_amount, from_currency, to_currency, provider
            )

        if converted_amount is None:
            raise HTTPException(status_code=400, detail="Unable to perform currency conversion")

        return converted_amount, exchange_rate, conversion_path

    @staticmethod
    async def _try_direct_conversion(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float | None, float, list[str]]:
        try:
            logger.info(f"Attempting direct conversion: {from_currency.abbreviation} to {to_currency.abbreviation}")
            converted_amount = await convert_currency(session, amount, from_currency, to_currency, provider)
            converted_amount = round(converted_amount, 2)
            exchange_rate = round(converted_amount / amount, 4)
            conversion_path = [from_currency.abbreviation, to_currency.abbreviation]
            logger.info(
                f"Direct conversion successful: {amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
            return converted_amount, exchange_rate, conversion_path
        except HTTPException as e:
            if e.status_code == 404:
                logger.warning(f"Direct conversion failed: {str(e)}")
                return None, 1.0, []
            raise

    @staticmethod
    async def _try_usd_conversion(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float | None, float, list[str]]:
        try:
            logger.warning(f"Direct conversion failed. Attempting conversion through USD.")
            usd_currency = await get_currency_by_abbreviation(session, "USD")

            logger.info(f"Converting {from_currency.abbreviation} to USD")
            amount_in_usd = await convert_currency(session, amount, from_currency, usd_currency, provider)

            logger.info(f"Converting USD to {to_currency.abbreviation}")
            converted_amount = await convert_currency(session, amount_in_usd, usd_currency, to_currency, provider)

            converted_amount = round(converted_amount, 2)
            exchange_rate = round(converted_amount / amount, 4)
            conversion_path = [from_currency.abbreviation, "USD", to_currency.abbreviation]
            logger.info(
                f"Conversion through USD successful: {amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
            return converted_amount, exchange_rate, conversion_path
        except HTTPException as e:
            logger.error(f"Conversion through USD failed: {str(e)}")
            return None, 1.0, []
