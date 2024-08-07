from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from core import logger
from core.models import Currency, TransferProvider
from core.services import convert_currency
from core.services import get_currency_by_abbreviation


# TODO: Currency-USD-currency transfer options search not working NEED TO FIX

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
        converted_amount = original_amount
        exchange_rate = 1.0
        conversion_path = []

        if to_currency.id == from_currency.id:
            logger.info(f"No conversion needed: {from_currency.abbreviation} to {to_currency.abbreviation}")
            return converted_amount, exchange_rate, [from_currency.abbreviation]

        try:
            logger.info(f"Attempting direct conversion: {from_currency.abbreviation} to {to_currency.abbreviation}")
            converted_amount = await convert_currency(session, original_amount, from_currency, to_currency, provider)
            converted_amount = round(converted_amount, 2)
            exchange_rate = round(converted_amount / original_amount, 4)
            conversion_path = [from_currency.abbreviation, to_currency.abbreviation]
            logger.info(
                f"Direct conversion successful: {original_amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
        except HTTPException as e:
            if e.status_code == 404:  # Exchange rate not found
                logger.warning(f"Direct conversion failed. Attempting conversion through USD.")
                try:
                    usd_currency = await get_currency_by_abbreviation(session, "USD")

                    logger.info(f"Converting {from_currency.abbreviation} to USD")
                    amount_in_usd = await convert_currency(session, original_amount, from_currency, usd_currency,
                                                           provider)

                    logger.info(f"Converting USD to {to_currency.abbreviation}")
                    converted_amount = await convert_currency(session, amount_in_usd, usd_currency, to_currency,
                                                              provider)

                    converted_amount = round(converted_amount, 2)
                    exchange_rate = round(converted_amount / original_amount, 4)
                    conversion_path = [from_currency.abbreviation, "USD", to_currency.abbreviation]
                    logger.info(
                        f"Conversion through USD successful: {original_amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
                except HTTPException as usd_error:
                    logger.error(f"Conversion through USD failed: {str(usd_error)}")
                    raise HTTPException(status_code=400, detail="Unable to perform currency conversion") from usd_error
            else:
                raise

        return converted_amount, exchange_rate, conversion_path
