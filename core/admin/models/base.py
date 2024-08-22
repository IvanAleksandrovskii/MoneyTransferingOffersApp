from typing import Any

from sqladmin import ModelView, action
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

from core import logger
from core.admin import async_sqladmin_db_helper


# TODO: fix exceptions handling for creation and update objects about unique constraints and ondelete exceptions
#  for currency if it's not allowed to delete a currency dew to county (local currency) relation.
#  (Only place no cascade delete for currency is countries relation, all other relations got cascade logic)

# TODO: Maybe need to work on the model Base or to solve it with some admin logic fixes
class BaseAdminModel(ModelView):
    column_list = ['is_active', 'id']
    column_sortable_list = ['is_active']
    column_filters = ['is_active']
    page_size = 50
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    async def get_form(self, form_class, obj: Any = None):
        return await super().get_form(form_class, obj)

    async def _process_action(self, request: Request, is_active: bool) -> None:
        pks = request.query_params.get("pks", "").split(",")
        if pks:
            try:
                async with AsyncSession(async_sqladmin_db_helper.engine) as session:
                    for pk in pks:
                        model = await session.get(self.model, pk)
                        if model:
                            model.is_active = is_active
                    await session.commit()
                logger.info(f"Successfully {'activated' if is_active else 'deactivated'} {len(pks)} objects")
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                await session.rollback()

    @action(
        name="activate",
        label="Activate",
        confirmation_message="Are you sure you want to activate selected %(model)s?",
        add_in_detail=True,
        add_in_list=True,
    )
    async def activate(self, request: Request) -> RedirectResponse:
        await self._process_action(request, True)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)

    @action(
        name="deactivate",
        label="Deactivate",
        confirmation_message="Are you sure you want to deactivate selected %(model)s?",
        add_in_detail=True,
        add_in_list=True,
    )
    async def deactivate(self, request: Request) -> RedirectResponse:
        await self._process_action(request, False)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)

    # TODO: Make error logging shorter?
    async def insert_model(self, request: Request, data: dict) -> Any:
        try:
            return await super().insert_model(request, data)
        except IntegrityError as e:
            error_msg = str(e).split('\n')[0]
            constraint = error_msg.split('"')[-2] if '"' in error_msg else "unknown"
            field = constraint.split('_')[-1] if '_' in constraint else constraint
            logger.error(f"IntegrityError in insert_model: {field} must be unique")
            raise HTTPException(status_code=400, detail=f"A record with this {field} already exists.")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in insert_model: {str(e).split('\n')[0]}")
            raise HTTPException(status_code=500, detail="An error occurred while creating the record.")
        except Exception as e:
            logger.error(f"Unexpected error in insert_model: {str(e).split('\n')[0]}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def update_model(self, request: Request, pk: Any, data: dict) -> Any:
        try:
            return await super().update_model(request, pk, data)
        except IntegrityError as e:
            error_msg = str(e).split('\n')[0]
            constraint = error_msg.split('"')[-2] if '"' in error_msg else "unknown"
            field = constraint.split('_')[-1] if '_' in constraint else constraint
            logger.error(f"IntegrityError in update_model: {field} must be unique")
            raise HTTPException(status_code=400, detail=f"A record with this {field} already exists.")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in update_model: {str(e).split('\n')[0]}")
            raise HTTPException(status_code=500, detail="An error occurred while updating the record.")
        except Exception as e:
            logger.error(f"Unexpected error in update_model: {str(e).split('\n')[0]}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def delete_model(self, request: Request, pk: Any) -> bool:
        try:
            result = await super().delete_model(request, pk)
            if result is None:
                logger.warning(f"Delete operation for pk {pk} returned None")
                return False
            return True
        except IntegrityError as e:
            error_message = str(e).split('\n')[0]
            logger.error(f"IntegrityError in delete_model: {error_message}")
            raise HTTPException(status_code=400, detail=error_message)
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in delete_model: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while deleting the record.")
        except Exception as e:
            logger.error(f"Unexpected error in delete_model: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")
