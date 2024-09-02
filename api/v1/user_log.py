from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from core.models import db_helper
from core.models import TgUser, TgUserLog
from core.schemas import TgUserCreate, TgUserLogCreate

router = APIRouter()


@router.post("/tg-user")
async def create_tg_user(user: TgUserCreate, db: AsyncSession = Depends(db_helper.session_getter)):
    db_user = TgUser(tg_user=user.tg_user)
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except IntegrityError:
        await db.rollback()
    return db_user


@router.post("/tg-user-log")
async def create_tg_user_log(log: TgUserLogCreate, db: AsyncSession = Depends(db_helper.session_getter)):
    # Check if user exists
    result = await db.execute(select(TgUser).filter(TgUser.tg_user == log.tg_user))
    user = result.scalar_one_or_none()
    if not user:
        user = TgUser(tg_user=log.tg_user)
        db.add(user)
        await db.flush()

    db_log = TgUserLog(tg_user=log.tg_user, url_log=log.url_log, amount_log=log.amount_log, currency_log=log.currency_log)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log
