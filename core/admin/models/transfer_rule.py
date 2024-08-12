from typing import Any
from urllib.parse import urlencode

from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import SelectMultipleField, validators
from wtforms.widgets import ListWidget, CheckboxInput

from core import logger
from core.admin import async_sqladmin_db_helper
from core.models import TransferRule, Document


class TransferRuleAdmin(ModelView, model=TransferRule):

    def __init__(self, *args, **kwargs):
        super().__init__()
        # self._processing = False

    column_list = [
        "formatted_transfer_rule",
        TransferRule.fee_percentage,
        TransferRule.is_active,
        TransferRule.id,
        TransferRule.provider_id,
        TransferRule.send_country_id,
        TransferRule.receive_country_id,
        TransferRule.transfer_currency_id,
        TransferRule.min_transfer_amount,
        TransferRule.max_transfer_amount,
    ]

    column_formatters = {
        "formatted_transfer_rule": lambda m, a:
        f"{m.provider.name} - {m.send_country.abbreviation} - {m.receive_country.abbreviation} - "
        f"{m.transfer_currency.abbreviation if m.transfer_currency else 'Unknown'} - {m.min_transfer_amount} - "
        f"{m.max_transfer_amount}",
        "provider": lambda m, a: str(m.provider),
        "send_country": lambda m, a: str(m.send_country),
        "receive_country": lambda m, a: str(m.receive_country),
        "transfer_currency": lambda m, a: str(m.transfer_currency),
    }

    form_columns = [
        'provider', 'send_country', 'receive_country', 'transfer_currency',
        'fee_percentage', 'min_transfer_amount', 'max_transfer_amount',
        'transfer_method', 'min_transfer_time', 'max_transfer_time', 'required_documents', 'is_active'
    ]

    form_args = {
        'send_country': {'validators': [validators.DataRequired()]},
        'receive_country': {'validators': [validators.DataRequired()]},
        'provider': {'validators': [validators.DataRequired()]},
        'transfer_currency': {'validators': [validators.DataRequired()]},
    }

    async def scaffold_form(self):
        form_class = await super().scaffold_form()
        form_class.required_documents = SelectMultipleField(
            'Required Documents',
            choices=await self._get_document_choices(),
            widget=ListWidget(prefix_label=False),
            option_widget=CheckboxInput(),
            coerce=self._coerce_document
        )
        return form_class

    def _coerce_document(self, value):
        if hasattr(value, 'id'):
            return str(value.id)
        return str(value)

    async def _get_document_choices(self):
        async with AsyncSession(async_sqladmin_db_helper.engine) as session:
            try:
                result = await session.execute(select(Document).where(Document.is_active == True))
                documents = result.scalars().all()
                return [(str(doc.id), doc.name) for doc in documents]
            finally:
                await session.close()

    async def get_one(self, _id):
        async with AsyncSession(async_sqladmin_db_helper.engine) as session:
            try:
                stmt = select(TransferRule).options(
                    selectinload(TransferRule.required_documents)
                ).filter_by(id=_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            finally:
                await session.close()

    async def edit_form(self, obj):
        form = await super().edit_form(obj)
        if obj and obj.required_documents:
            form.required_documents.data = [str(doc.id) for doc in obj.required_documents]
        return form

    async def insert_model(self, request: Request, data: dict) -> Any:
        logger.info("Custom insert_model method called")
        async with AsyncSession(async_sqladmin_db_helper.engine) as session:
            try:
                # Check if rule with same send_country, receive_country, provider, transfer_currency already exists
                existing_rule = await session.execute(
                    select(TransferRule).filter_by(
                        send_country_id=data['send_country'],
                        receive_country_id=data['receive_country'],
                        provider_id=data['provider'],
                        transfer_currency_id=data['transfer_currency']
                    )
                )
                existing_rule = existing_rule.scalar_one_or_none()

                if existing_rule:
                    logger.info(f"Updating existing TransferRule with id: {existing_rule.id}")
                    model = existing_rule
                else:
                    logger.info("Creating new TransferRule")
                    model = TransferRule()
                    session.add(model)

                # Update Model Fields
                for key, value in data.items():
                    if key == 'required_documents':
                        model.required_documents = []
                        for doc_id in value:
                            document = await session.get(Document, doc_id)
                            if document:
                                model.required_documents.append(document)
                    elif key in ['send_country', 'receive_country', 'provider', 'transfer_currency']:
                        setattr(model, f"{key}_id", str(value))
                    else:
                        setattr(model, key, value)

                await session.commit()
                await session.refresh(model)
                logger.info(
                    f"TransferRule {'updated' if existing_rule else 'created'} successfully with id: {model.id}")

                return model

            except IntegrityError as e:
                await session.rollback()
                logger.error(f"IntegrityError in insert_model: {str(e)}")
                raise ValueError("A transfer rule with these parameters already exists.")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error in insert_model: {str(e)}")
                raise

    def get_save_redirect_url(self, request: Request, obj: Any, is_created: bool) -> str:
        if is_created:
            return request.url_for("admin:list", identity=self.identity)
        return request.url_for("admin:detail", identity=self.identity, pk=obj.id)

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        if is_created:
            logger.info("Created transfer rule successfully")
        else:
            logger.info("Updated transfer rule successfully")
