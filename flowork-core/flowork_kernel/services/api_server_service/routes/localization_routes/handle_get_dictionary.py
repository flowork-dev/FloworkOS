########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\localization_routes\handle_get_dictionary.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    lang_code = request.match_info.get('lang_code')
    loc = hub.service_instance.loc
    if not loc:
        await hub.execute_async('logger', 'Gracefully handling missing LocalizationManager service.', 'INFO')
        return await hub.execute_async('_json_response', {})
    dictionary = loc.languages.get(lang_code)
    if dictionary:
        return await hub.execute_async('_json_response', dictionary)
    else:
        en_dictionary = loc.languages.get('en')
        if en_dictionary:
            return await hub.execute_async('_json_response', en_dictionary)
        else:
            return await hub.execute_async('_json_response', {})
