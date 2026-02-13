########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\get_embedding.py total lines 35 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

def run(hub, text: str, endpoint_id: str = None, **kwargs):
    """
    Atomic Cell: Mengambil vektor embedding dari provider AI.
    Wajib digunakan sebelum memasukkan data ke NeuralKnowledge Router.
    """
    target = endpoint_id

    if not target:
        for pid, p in hub.loaded_providers.items():
            if hasattr(p, 'get_embedding'):
                target = pid
                break

    if not target:
        hub.logger.error("[Embedding] No capable AI provider found for embedding task.")
        return []

    hub.logger.info(f"[Embedding] Requesting vector from: {target}")

    if target in hub.loaded_providers:
        p = hub.loaded_providers[target]
        if hasattr(p, 'get_embedding'):
            return p.get_embedding(text)
        else:
            hub.logger.warning(f"[Embedding] Provider {target} does not support embeddings.")
            return []

    hub.logger.error(f"[Embedding] Endpoint {target} not found in loaded providers.")
    return []
