import os.path
from importlib import import_module

from django.apps import AppConfig, apps


class HeatherrConfig(AppConfig):

    name = 'heatherr'

    def ready(self):
        for app in apps.get_app_configs():
            if os.path.isfile(os.path.join(app.path, 'commands.py')):
                import_module('%s.commands' % (app.module.__name__,))
