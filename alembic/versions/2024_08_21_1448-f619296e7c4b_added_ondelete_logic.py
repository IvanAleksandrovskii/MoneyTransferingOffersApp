"""added ondelete logic

Revision ID: f619296e7c4b
Revises: 4573e3b0eb75
Create Date: 2024-08-21 14:48:42.344979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f619296e7c4b'
down_revision: Union[str, None] = '4573e3b0eb75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_countries_local_currency_id_currencies', 'countries', type_='foreignkey')
    op.create_foreign_key(op.f('fk_countries_local_currency_id_currencies'), 'countries', 'currencies', ['local_currency_id'], ['id'], ondelete='RESTRICT')
    op.drop_constraint('fk_provider_exchange_rates_from_currency_id_currencies', 'provider_exchange_rates', type_='foreignkey')
    op.drop_constraint('fk_provider_exchange_rates_to_currency_id_currencies', 'provider_exchange_rates', type_='foreignkey')
    op.create_foreign_key(op.f('fk_provider_exchange_rates_from_currency_id_currencies'), 'provider_exchange_rates', 'currencies', ['from_currency_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_provider_exchange_rates_to_currency_id_currencies'), 'provider_exchange_rates', 'currencies', ['to_currency_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('fk_transfer_rule_documents_document_id_documents', 'transfer_rule_documents', type_='foreignkey')
    op.drop_constraint('fk_transfer_rule_documents_transfer_rule_id_transfer_rules', 'transfer_rule_documents', type_='foreignkey')
    op.create_foreign_key(op.f('fk_transfer_rule_documents_document_id_documents'), 'transfer_rule_documents', 'documents', ['document_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_transfer_rule_documents_transfer_rule_id_transfer_rules'), 'transfer_rule_documents', 'transfer_rules', ['transfer_rule_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('fk_transfer_rules_send_country_id_countries', 'transfer_rules', type_='foreignkey')
    op.drop_constraint('fk_transfer_rules_transfer_currency_id_currencies', 'transfer_rules', type_='foreignkey')
    op.drop_constraint('fk_transfer_rules_receive_country_id_countries', 'transfer_rules', type_='foreignkey')
    op.create_foreign_key(op.f('fk_transfer_rules_send_country_id_countries'), 'transfer_rules', 'countries', ['send_country_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_transfer_rules_transfer_currency_id_currencies'), 'transfer_rules', 'currencies', ['transfer_currency_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_transfer_rules_receive_country_id_countries'), 'transfer_rules', 'countries', ['receive_country_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_transfer_rules_receive_country_id_countries'), 'transfer_rules', type_='foreignkey')
    op.drop_constraint(op.f('fk_transfer_rules_transfer_currency_id_currencies'), 'transfer_rules', type_='foreignkey')
    op.drop_constraint(op.f('fk_transfer_rules_send_country_id_countries'), 'transfer_rules', type_='foreignkey')
    op.create_foreign_key('fk_transfer_rules_receive_country_id_countries', 'transfer_rules', 'countries', ['receive_country_id'], ['id'])
    op.create_foreign_key('fk_transfer_rules_transfer_currency_id_currencies', 'transfer_rules', 'currencies', ['transfer_currency_id'], ['id'])
    op.create_foreign_key('fk_transfer_rules_send_country_id_countries', 'transfer_rules', 'countries', ['send_country_id'], ['id'])
    op.drop_constraint(op.f('fk_transfer_rule_documents_transfer_rule_id_transfer_rules'), 'transfer_rule_documents', type_='foreignkey')
    op.drop_constraint(op.f('fk_transfer_rule_documents_document_id_documents'), 'transfer_rule_documents', type_='foreignkey')
    op.create_foreign_key('fk_transfer_rule_documents_transfer_rule_id_transfer_rules', 'transfer_rule_documents', 'transfer_rules', ['transfer_rule_id'], ['id'])
    op.create_foreign_key('fk_transfer_rule_documents_document_id_documents', 'transfer_rule_documents', 'documents', ['document_id'], ['id'])
    op.drop_constraint(op.f('fk_provider_exchange_rates_to_currency_id_currencies'), 'provider_exchange_rates', type_='foreignkey')
    op.drop_constraint(op.f('fk_provider_exchange_rates_from_currency_id_currencies'), 'provider_exchange_rates', type_='foreignkey')
    op.create_foreign_key('fk_provider_exchange_rates_to_currency_id_currencies', 'provider_exchange_rates', 'currencies', ['to_currency_id'], ['id'])
    op.create_foreign_key('fk_provider_exchange_rates_from_currency_id_currencies', 'provider_exchange_rates', 'currencies', ['from_currency_id'], ['id'])
    op.drop_constraint(op.f('fk_countries_local_currency_id_currencies'), 'countries', type_='foreignkey')
    op.create_foreign_key('fk_countries_local_currency_id_currencies', 'countries', 'currencies', ['local_currency_id'], ['id'])
    # ### end Alembic commands ###
