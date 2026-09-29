# -*- coding: utf-8 -*-
"""
Storage de Dropbox que arregla el bug de Windows donde se agrega
la letra de la unidad (C:/) a las rutas. En Linux funciona normal.
"""
import os
from django.utils._os import safe_join
from storages.backends.dropbox import DropBoxStorage as BaseDropBoxStorage


class WindowsSafeDropBoxStorage(BaseDropBoxStorage):
    def _full_path(self, name):
        if name == "/":
            name = ""
        if os.name == "nt":  # Windows
            return os.path.join(self.root_path, name).replace("\\", "/")
        return safe_join(self.root_path, name).replace("\\", "/")
