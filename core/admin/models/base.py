from typing import Any

from sqladmin import ModelView, action
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

from core import logger
from core.admin import async_sqladmin_db_helper


# TODO: fix logging and exceptions handling for creation and update objects about unique constraints violations
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

    async def insert_model(self, request: Request, data: dict) -> Any:
        try:
            return await super().insert_model(request, data)
        except IntegrityError:
            logger.warning(f"Attempt to violate unique constraint when creating {self.name}")
            raise HTTPException(status_code=400, detail=f"A {self.name.lower()} with these details already exists.")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in insert_model for {self.name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred while creating the {self.name.lower()}.")
        except Exception as e:
            logger.error(f"Unexpected error in insert_model for {self.name}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def update_model(self, request: Request, pk: Any, data: dict) -> Any:
        try:
            return await super().update_model(request, pk, data)
        except IntegrityError:
            logger.warning(f"Attempt to violate unique constraint when updating {self.name}")
            raise HTTPException(status_code=400, detail=f"A {self.name.lower()} with these details already exists.")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in update_model for {self.name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred while updating the {self.name.lower()}.")
        except Exception as e:
            logger.error(f"Unexpected error in update_model for {self.name}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def delete_model(self, request: Request, pk: Any) -> Any:
        try:
            result = await super().delete_model(request, pk)
            if result is None:
                logger.error(f"Delete operation for {self.name} with pk {pk} returned None")
                return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)
            return result
        except IntegrityError:
            logger.error(f"Attempt to delete {self.name} with pk {pk} that has associated records")
            error = f"This {self.name.lower()} cannot be deleted because it is associated with other records."
            return RedirectResponse(
                request.url_for("admin:list", identity=self.identity).include_query_params(error=error),
                status_code=302
            )
        except Exception as e:
            logger.error(f"Unexpected error when deleting {self.name} with pk {pk}: {str(e)}")
            error = f"An unexpected error occurred while deleting the {self.name.lower()}."
            return RedirectResponse(
                request.url_for("admin:list", identity=self.identity).include_query_params(error=error),
                status_code=302
            )
