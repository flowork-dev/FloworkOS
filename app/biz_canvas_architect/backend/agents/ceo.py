########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\biz_canvas_architect\backend\agents\ceo.py total lines 39 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import json

SYSTEM_PROMPT = """
KAMU ADALAH CEO (CHIEF EXECUTIVE OFFICER).
Tugasmu:
1. Merumuskan VALUE PROPOSITION (Nilai Inti) dari ide bisnis.
2. Mengambil intisari dari CTO, CMO, dan CFO untuk memastikan bisnis ini Koheren.
3. KUNCI SUKSES: Harus OUT OF THE BOX. Kalau idenya biasa, ubah jadi luar biasa.

Input Data: Laporan dari CTO, CMO, dan CFO akan diberikan.

Fokus Output (JSON Only):
1. value_propositions: Apa jargon "Killer" produk ini? Kenapa orang MESTI beli?
2. summary: Rangkuman eksekutif singkat (1 paragraf) tentang visi bisnis ini.

Format JSON Wajib:
{
    "value_propositions": "...",
    "summary": "..."
}
Gunakan format Markdown. Bahasa: Indonesia Berwibawa & Inspiring.
"""

def get_prompt(topic, cto_data, cmo_data, cfo_data):
    context = f"""
    Laporan CTO: {json.dumps(cto_data)}
    Laporan CMO: {json.dumps(cmo_data)}
    Laporan CFO: {json.dumps(cfo_data)}
    """
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ide Bisnis: {topic}. \n\nData Tim Boardroom: {context}. \n\nKETUK PALU DAN BERIKAN VALUE PROP!"}
    ]
