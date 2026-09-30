# -*- coding: utf-8 -*-
"""
Storage de Dropbox que:
1. Arregla el bug de Windows donde se agrega la letra de la unidad (C:/).
2. Lee DROPBOX_ACCESS_TOKEN del entorno en tiempo de instanciacion
   (no cuando se importa settings.py), para que funcione aunque la
   variable se haya agregado despues del arranque.
"""
import os
from django.utils._os import safe_join
from storages.backends.dropbox import DropBoxStorage as BaseDropBoxStorage


class WindowsSafeDropBoxStorage(BaseDropBoxStorage):
    def __init__(self, **settings):
        # Leer el token del entorno SI no viene explicito
        if not settings.get('oauth2_access_token'):
            token = os.environ.get('DROPBOX_ACCESS_TOKEN', '').strip()
            if token:
                settings['oauth2_access_token'] = token
        super().__init__(**settings)

    def _full_path(self, name):
        if name == "/":
            name = ""
        if os.name == "nt":  # Windows
            return os.path.join(self.root_path, name).replace("\\", "/")
        return safe_join(self.root_path, name).replace("\\", "/")
