########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\neural_knowledge_router\search_knowledge.py total lines 55 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import json
import math

def cosine_similarity(v1, v2):
    """Menghitung seberapa mirip dua vektor (0 s/d 1)"""
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0: return 0.0
    return dot_product / (magnitude1 * magnitude2)

def run(hub, query: str, user_id: str, limit: int = 3, threshold: float = 0.7):
    """
    Melakukan Semantic Search ke Neural Vault.
    """
    hub.logger.info(f"[RAG] Searching knowledge for user {user_id}: '{query}'")

    query_vector = hub.ai_manager.execute_sync("get_embedding", query)
    if not query_vector:
        return []

    sql = """
        SELECT nk.content, nk.source, kv.vector_data
        FROM NeuralKnowledge nk
        JOIN KnowledgeVectors kv ON nk.id = kv.knowledge_id
        WHERE nk.user_id = ?
    """
    rows = hub.db.execute_app_query(sql, (user_id,))

    results = []

    for row in rows:
        content = row[0]
        source = row[1]
        stored_vector = json.loads(row[2])

        score = cosine_similarity(query_vector, stored_vector)

        if score >= threshold:
            results.append({
                "content": content,
                "source": source,
                "score": score
            })

    results.sort(key=lambda x: x['score'], reverse=True)

    return results[:limit]
