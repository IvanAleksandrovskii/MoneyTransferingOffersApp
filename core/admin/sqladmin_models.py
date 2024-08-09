from datetime import timezone
from typing import Any

from sqladmin import ModelView, action
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import validators
from wtforms.validators import ValidationError

from core.admin.sqladmin_db_helper import sync_sqladmin_db_helper
from core.models import Country
from core.models import Currency
from core.models import TransferProvider
from core.models import TransferRule
from core.models import ProviderExchangeRate
from core import logger


def format_exchange_rate(model, name):  # Do not delete name form here in is not unused (!), needed for formatting
    return f"{model.provider.name} - {model.from_currency.abbreviation} - {model.to_currency.abbreviation}"


def format_transfer_rule(model, name):  # Do not delete name form here in is not unused (!), needed for formatting
    return (f"{model.provider.name} - {model.send_country.name} - {model.receive_country.name} - "
            f"{model.transfer_currency.abbreviation if model.transfer_currency else 'Unknown'} - "
            f"{model.min_transfer_amount} - {model.max_transfer_amount}")


class BaseAdminModel(ModelView):
    column_list = ['id', 'is_active']
    column_sortable_list = ['is_active']
    column_filters = ['is_active']
    page_size = 50
    can_create = True
    can_edit = True
    can_view_details = True

    def _process_action(self, request: Request, is_active: bool) -> None:
        pks = request.query_params.get("pks", "").split(",")
        if pks:
            try:
                with Session(sync_sqladmin_db_helper.engine) as session:
                    for pk in pks:
                        model = session.get(self.model, pk)
                        if model:
                            model.is_active = is_active
                    session.commit()
                logger.info(f"Successfully {'activated' if is_active else 'deactivated'} {len(pks)} objects")
            except SQLAlchemyError as e:
                logger.error(f"An error occurred: {str(e)}")
                session.rollback()

    @action(
        name="activate",
        label="Activate",
        confirmation_message="Are you sure you want to activate selected %(model)s?",
        add_in_detail=True,
        add_in_list=True,
    )
    def activate(self, request: Request) -> RedirectResponse:
        self._process_action(request, True)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)

    @action(
        name="deactivate",
        label="Deactivate",
        confirmation_message="Are you sure you want to deactivate selected %(model)s?",
        add_in_detail=True,
        add_in_list=True,
    )
    def deactivate(self, request: Request) -> RedirectResponse:
        self._process_action(request, False)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)


class CountryAdmin(BaseAdminModel, model=Country):
    column_list = BaseAdminModel.column_list + [Country.name, Country.local_currency_id]
    column_searchable_list = [Country.name]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Country.name]
    column_filters = BaseAdminModel.column_filters + [Country.name, Country.local_currency_id]
    form_columns = ['name', 'local_currency', 'is_active']
    form_args = {
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'name': {
            'placeholder': 'Enter country name'
        }
    }
    name = "Country"
    name_plural = "Countries"
    category = "Global"
    can_delete = False

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        logger.info(f"{'Created' if is_created else 'Updated'} country: {model.name}")


class CurrencyAdmin(BaseAdminModel, model=Currency):
    column_list = BaseAdminModel.column_list + [Currency.abbreviation, Currency.name, Currency.symbol]
    column_searchable_list = [Currency.name, Currency.abbreviation]
    column_sortable_list = BaseAdminModel.column_sortable_list + [Currency.name, Currency.abbreviation]
    column_filters = BaseAdminModel.column_filters + [Currency.name, Currency.abbreviation]
    form_excluded_columns = ['countries']
    form_args = {
        'abbreviation': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=3)]
        },
        'symbol': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=5)]
        },
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'abbreviation': {
            'placeholder': 'e.g. USD'
        },
        'symbol': {
            'placeholder': 'e.g. $'
        },
        'name': {
            'placeholder': 'e.g. US Dollar'
        }
    }
    name = "Currency"
    name_plural = "Currencies"
    category = "Global"
    can_delete = False


class TransferProviderAdmin(BaseAdminModel, model=TransferProvider):
    column_list = BaseAdminModel.column_list + [TransferProvider.name, TransferProvider.url]
    column_searchable_list = [TransferProvider.name]
    column_sortable_list = BaseAdminModel.column_sortable_list + [TransferProvider.name]
    column_filters = BaseAdminModel.column_filters + [TransferProvider.name]
    form_excluded_columns = ['exchange_rates', 'transfer_rules']
    form_args = {
        'url': {
            'validators': [validators.DataRequired(), validators.URL(), validators.Length(max=255)]
        },
        'name': {
            'validators': [validators.DataRequired(), validators.Length(min=1, max=100)]
        }
    }
    form_widget_args = {
        'url': {
            'placeholder': 'https://example.com'
        },
        'name': {
            'placeholder': 'Enter provider name'
        }
    }
    category = "Providers"


def validate_min_max(form, field):
    if form.min_transfer_amount.data is not None and form.max_transfer_amount.data is not None:
        if form.min_transfer_amount.data > form.max_transfer_amount.data:
            raise ValidationError('Minimum transfer amount cannot be greater than maximum transfer amount')


class TransferRuleAdmin(BaseAdminModel, model=TransferRule):
    column_list = BaseAdminModel.column_list + [
        "formatted_transfer_rule",
        TransferRule.fee_percentage,
        TransferRule.min_transfer_amount,
        TransferRule.max_transfer_amount,
        TransferRule.send_country_id,
        TransferRule.receive_country_id,
        TransferRule.transfer_currency_id,
        TransferRule.provider_id
    ]
    column_formatters = {
        "formatted_transfer_rule": format_transfer_rule
    }
    column_searchable_list = [TransferRule.transfer_method]
    column_sortable_list = BaseAdminModel.column_sortable_list + [
        TransferRule.fee_percentage,
        TransferRule.min_transfer_amount,
        TransferRule.max_transfer_amount
    ]
    column_filters = BaseAdminModel.column_filters + [
        TransferRule.send_country_id,
        TransferRule.receive_country_id,
        TransferRule.transfer_currency_id,
        TransferRule.provider_id,
        TransferRule.transfer_method
    ]
    form_args = {
        'fee_percentage': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0, max=99.99)]
        },
        'min_transfer_amount': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0), validate_min_max]
        },
        'max_transfer_amount': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0)]
        }
    }
    name = "Transfer Rule"
    category = "Providers"

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        # This method is kept for compatibility, but validation should now happen at the form level
        pass


class ProviderExchangeRateAdmin(BaseAdminModel, model=ProviderExchangeRate):
    column_list = BaseAdminModel.column_list + [
        "formatted_exchange_rate",
        ProviderExchangeRate.rate,
        ProviderExchangeRate.last_updated,
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id
    ]
    column_formatters = {
        "last_updated": lambda m, a: m.last_updated.strftime("%Y-%m-%d %H:%M:%S") if m.last_updated else "",
        "formatted_exchange_rate": format_exchange_rate
    }
    column_sortable_list = BaseAdminModel.column_sortable_list + [ProviderExchangeRate.rate,
                                                                  ProviderExchangeRate.last_updated]
    column_filters = BaseAdminModel.column_filters + [
        ProviderExchangeRate.provider_id,
        ProviderExchangeRate.from_currency_id,
        ProviderExchangeRate.to_currency_id
    ]
    form_excluded_columns = ["last_updated"]
    form_args = {
        'rate': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0)]
        }
    }
    name = "Provider Exchange Rate"
    category = "Providers"
