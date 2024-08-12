from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from wtforms import SelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput

from core import logger
from core.admin.models.base import BaseAdminModel
from core.models import TransferRule, db_helper, Document


class TransferRuleAdmin(BaseAdminModel, model=TransferRule):
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
        "formatted_transfer_rule": lambda m, a: f"{m.provider.name} - {m.send_country.name} - {m.receive_country.name} - {m.transfer_currency.abbreviation if m.transfer_currency else 'Unknown'} - {m.min_transfer_amount} - {m.max_transfer_amount}",
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
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(Document).where(Document.is_active == True))
                documents = result.scalars().all()
                return [(str(doc.id), doc.name) for doc in documents]
            finally:
                await session.close()

    async def get_one(self, _id):
        async for session in db_helper.session_getter():
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

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        async with db_helper.session_factory() as session:
            try:
                # Get the fresh model from the database
                if is_created:
                    fresh_model = TransferRule()
                    session.add(fresh_model)
                else:
                    fresh_model = await session.get(TransferRule, model.id,
                                                    options=[selectinload(TransferRule.required_documents)])

                if not fresh_model:
                    raise ValueError(f"TransferRule with id {model.id} not found")

                for key, value in data.items():
                    if key == 'required_documents':
                        new_doc_ids = set(self._coerce_document(doc_id) for doc_id in value)
                        current_doc_ids = set(str(doc.id) for doc in fresh_model.required_documents)

                        # Delete documents, which are not in the new set
                        docs_to_remove = current_doc_ids - new_doc_ids
                        for doc_id in docs_to_remove:
                            doc = next((d for d in fresh_model.required_documents if str(d.id) == doc_id), None)
                            if doc:
                                fresh_model.required_documents.remove(doc)

                        # Add new documents, check for duplicates
                        docs_to_add = new_doc_ids - current_doc_ids
                        for doc_id in docs_to_add:
                            doc = await session.get(Document, doc_id)
                            if doc:
                                fresh_model.required_documents.append(doc)

                    elif key in ['send_country', 'receive_country', 'provider', 'transfer_currency']:
                        setattr(fresh_model, f"{key}_id", str(value))
                    else:
                        setattr(fresh_model, key, value)

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.exception(f"Error in on_model_change: {str(e)}")
                raise e

        await super().on_model_change(data, fresh_model, is_created, request)
