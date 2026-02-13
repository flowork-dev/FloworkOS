########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\get.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, key, fallback=None, **kwargs):
    stripped_key = key.strip()
    if stripped_key.startswith('loc.'):
        stripped_key = stripped_key[4:]
    lang_data = hub.languages.get(hub.current_lang)
    if lang_data and stripped_key in lang_data:
        text = lang_data[stripped_key]
        return text.format(**kwargs) if kwargs else text
    lang_data_en = hub.languages.get('en')
    if lang_data_en and stripped_key in lang_data_en:
        return lang_data_en[stripped_key].format(**kwargs) if kwargs else lang_data_en[stripped_key]
    if fallback is not None:
        if isinstance(fallback, str):
            return fallback.format(**kwargs) if kwargs else fallback
        return fallback
    return f'[{key}]'
