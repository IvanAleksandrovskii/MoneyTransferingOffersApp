from sqladmin import ModelView
from core.models import TgUser, TgUserLog


class TgUserAdmin(ModelView, model=TgUser):
    column_list = [TgUser.id, TgUser.tg_user, TgUser.created_at]
    column_searchable_list = [TgUser.id, TgUser.tg_user]
    column_sortable_list = [TgUser.id, TgUser.created_at]
    column_filters = [TgUser.tg_user]
    can_create = False
    can_edit = False
    can_delete = True
    name = "Telegram User"
    name_plural = "Telegram Users"
    category = "Telegram"


class TgUserLogAdmin(ModelView, model=TgUserLog):
    column_list = [TgUserLog.id, TgUserLog.tg_user, TgUserLog.url_log, TgUserLog.amount_log, TgUserLog.currency_log,
                   TgUserLog.send_country_log, TgUserLog.receive_country_log, TgUserLog.created_at]
    column_searchable_list = [TgUserLog.tg_user, TgUserLog.url_log, TgUserLog.currency_log,
                              TgUserLog.send_country_log, TgUserLog.receive_country_log, ]
    column_sortable_list = [TgUserLog.id, TgUserLog.tg_user, TgUserLog.url_log, TgUserLog.amount_log,
                            TgUserLog.send_country_log, TgUserLog.receive_country_log, TgUserLog.created_at]
    column_filters = [TgUserLog.tg_user, TgUserLog.currency_log, TgUserLog.url_log, TgUserLog.amount_log,
                      TgUserLog.send_country_log, TgUserLog.receive_country_log, TgUserLog.created_at]
    can_create = False
    can_edit = False
    can_delete = True
    name = "Telegram User Log"
    name_plural = "Telegram User Logs"
    category = "Telegram"
