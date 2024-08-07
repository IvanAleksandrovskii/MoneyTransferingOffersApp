from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import logger
from core.models import Currency, TransferProvider, ProviderExchangeRate


async def convert_currency(session: AsyncSession, amount: float, from_currency: Currency, to_currency: Currency,
                           provider: TransferProvider) -> float:
    logger.info(
        f"Converting {amount} from {from_currency.abbreviation} to {to_currency.abbreviation} using provider {provider.name}")

    try:
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
        converted_amount = amount * rate.rate
        logger.info(f"Converted amount: {amount} {from_currency.abbreviation} = {converted_amount} {to_currency.abbreviation}")
        return converted_amount

    except Exception as e:
        logger.error(f"Error during currency conversion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during currency conversion"
        )
