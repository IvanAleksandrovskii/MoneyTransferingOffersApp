from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper
from core.models.transfer_rule import TransferRule
from core.models.transfer_provider import TransferProvider

router = APIRouter()


@router.get("/providers")
async def get_providers(session: AsyncSession = Depends(db_helper.session_getter)):
    providers = await session.execute(select(TransferProvider))
    return providers.scalars().all()


@router.get("/transfer-rules")
async def get_transfer_rules(
    from_country: str,
    to_country: str,
    amount: float,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    rules = await session.execute(
        select(TransferRule).filter(
            TransferRule.send_country.has(name=from_country),
            TransferRule.receive_country.has(name=to_country),
            TransferRule.min_transfer_amount <= amount,
            TransferRule.max_transfer_amount >= amount
        )
    )
    return rules.scalars().all()
