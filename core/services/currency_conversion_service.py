from sqlalchemy.ext.asyncio import AsyncSession

from core import logger
from core.models import Currency, TransferProvider
from core.services import convert_currency
from core.services import get_currency_by_abbreviation


class CurrencyConversionService:
    @staticmethod
    async def convert_amount(
            session: AsyncSession,
            amount: float,
            from_currency: Currency,
            to_currency: Currency,
            provider: TransferProvider
    ) -> tuple[float, float, list[str]]:
        """
        Convert an amount from one currency to another using the specified provider's exchange rates.
        Troughs an exception if the direct conversion fails, uses currency-USD-currency for that case.
        Args:
            session (AsyncSession): The database session.
            amount (float): The amount to convert.
            from_currency (Currency): The source currency.
            to_currency (Currency): The target currency.
            provider (TransferProvider): The transfer provider to use for conversion.

        Returns:
            tuple: A tuple containing:
                - converted_amount (float): The amount in the target currency.
                - exchange_rate (float): The exchange rate used for conversion.
                - conversion_path (list[str]): The path of currency conversions.
        """
        # Round the original amount to 2 decimal places
        original_amount = round(amount, 2)
        converted_amount = original_amount
        exchange_rate = 1.0
        conversion_path = []

        # Only proceed with conversion if currencies are different
        if to_currency.id != from_currency.id:
            try:
                # Attempt direct conversion between currencies
                converted_amount = await convert_currency(session, original_amount, from_currency, to_currency,
                                                          provider)
                converted_amount = round(converted_amount, 2)
                exchange_rate = round(converted_amount / original_amount, 3)
                conversion_path = [from_currency.abbreviation, to_currency.abbreviation]
            except Exception as e:
                logger.exception("Failed to convert currency: %s", e)

                # If direct conversion fails, try conversion through USD
                usd_currency = await get_currency_by_abbreviation(session, "USD")

                # Convert from source currency to USD
                amount_in_usd = await convert_currency(session, original_amount, from_currency, usd_currency, provider)

                # Convert from USD to target currency
                converted_amount = await convert_currency(session, amount_in_usd, usd_currency, to_currency, provider)

                converted_amount = round(converted_amount, 2)
                exchange_rate = round(converted_amount / original_amount, 3)
                conversion_path = [from_currency.abbreviation, "USD", to_currency.abbreviation]

        return converted_amount, exchange_rate, conversion_path
