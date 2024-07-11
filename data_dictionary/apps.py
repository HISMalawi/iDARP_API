import os

from django.apps import AppConfig


class DataDictionaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_dictionary'

    def ready(self):
        if os.environ.get('RUN_MAIN'):  # To avoid running it with the auto-reloader spawned process in development
            from data_requests.jobs import approval_reminder
            approval_reminder.start()
