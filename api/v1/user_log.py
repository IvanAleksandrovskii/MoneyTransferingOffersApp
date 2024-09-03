from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from core import logger
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
    try:
        # Check if user exists
        result = await db.execute(select(TgUser).filter(TgUser.tg_user == log.tg_user))
        user = result.scalar_one_or_none()
        if not user:
            user = TgUser(tg_user=log.tg_user)
            db.add(user)
            await db.flush()

        # Create log entry
        db_log = TgUserLog(
            tg_user=log.tg_user,
            url_log=log.url_log,
            amount_log=log.amount_log if log.amount_log else None,
            currency_log=log.currency_log if log.currency_log else None,
            send_country_log=log.send_country_log if log.send_country_log else None,
            receive_country_log=log.receive_country_log if log.receive_country_log else None
        )
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        return db_log
    except IntegrityError:
        await db.rollback()
        logger.warning(f"Integrity error when creating log for user {log.tg_user}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating log for user {log.tg_user}: {str(e)}")
