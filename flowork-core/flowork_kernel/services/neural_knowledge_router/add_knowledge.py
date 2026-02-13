########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\neural_knowledge_router\add_knowledge.py total lines 56 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import json

def run(hub, content: str, user_id: str, source: str = "manual", tags: dict = None):
    """
    Atomic Cell: Menambahkan informasi baru ke Neural Knowledge Base.
    Proses: Simpan teks -> Ambil Embedding -> Simpan Vektor.
    """
    hub.logger.info(f"[RAG] Adding new knowledge for user {user_id} from {source}")

    vector = hub.ai_manager.execute_sync("get_embedding", content)

    if not vector:
        hub.logger.error("[RAG] Failed to generate embedding. Knowledge not saved.")
        return False

    now = time.time()
    tags_str = json.dumps(tags) if tags else "{}"

    try:
        sql_content = """
            INSERT INTO NeuralKnowledge (user_id, content, source, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        hub.db.execute_app_query(sql_content, (user_id, content, source, tags_str, now, now))

        sql_get_id = "SELECT id FROM NeuralKnowledge WHERE user_id = ? AND created_at = ? LIMIT 1"
        rows = hub.db.execute_app_query(sql_get_id, (user_id, now))

        if not rows:
            hub.logger.error("[RAG] Failed to retrieve knowledge ID after insert.")
            return False

        knowledge_id = rows[0][0]

        vector_str = json.dumps(vector)
        provider_id = "default_rag_provider"

        sql_vector = """
            INSERT INTO KnowledgeVectors (knowledge_id, vector_data, provider_id)
            VALUES (?, ?, ?)
        """
        hub.db.execute_app_query(sql_vector, (knowledge_id, vector_str, provider_id))

        hub.logger.info(f"[RAG] ✅ Knowledge indexed successfully. ID: {knowledge_id}")
        return True

    except Exception as e:
        hub.logger.error(f"[RAG] Indexing Error: {e}")
        return False
