from sqlalchemy import select

from core import logger
from core.models import TgUser, db_helper


class UserService:

    @staticmethod
    async def create_user(tg_user: str, username: str | None) -> TgUser:
        async for session in db_helper.session_getter():
            try:
                # Check if user exists
                result = await session.execute(select(TgUser).where(TgUser.tg_user == tg_user))
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    logger.info("User %s already exists", tg_user)
                    return existing_user

                user = TgUser(tg_user=tg_user, username=username, is_superuser=False)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user

            except Exception as e:
                logger.exception(f"Error in create_user: {e}")
                await session.rollback()
            finally:
                await session.close()

    @staticmethod
    async def get_user(tg_user: str) -> TgUser | None:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(TgUser).where(TgUser.tg_user == tg_user))
                return result.scalar_one_or_none()
            except Exception as e:
                logger.exception(f"Error in get_user: {e}")
            finally:
                await session.close()

    @staticmethod
    async def get_all_users() -> list[TgUser]:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(TgUser))
                return result.scalars().unique().all()
            except Exception as e:
                logger.exception(f"Error in get_all_users: {e}")
            finally:
                await session.close()

    @classmethod
    async def is_superuser(cls, chat_id: str) -> bool:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(TgUser).where(TgUser.tg_user == chat_id))
                user = result.scalar_one_or_none()
                return user is not None and user.is_superuser
            except Exception as e:
                logger.exception(f"Error in is_superuser: {e}")
            finally:
                await session.close()
