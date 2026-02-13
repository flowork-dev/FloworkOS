########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\factories\ParserFactory.py total lines 15 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

class ParserFactory:

    @staticmethod
    def create_parser(kernel, formatter_id: str):

        formatter_manager = kernel.get_service("formatter_manager_service")
        if formatter_manager:
            return formatter_manager.get_formatter(formatter_id)
        return None
