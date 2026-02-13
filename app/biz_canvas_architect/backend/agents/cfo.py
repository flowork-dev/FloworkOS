########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\biz_canvas_architect\backend\agents\cfo.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import json

SYSTEM_PROMPT = """
KAMU ADALAH CFO (CHIEF FINANCIAL OFFICER) YANG KAPITALIS SEJATI.
Tugasmu: Memastikan bisnis ini CUAN GEDE dan COST TIPIS.
Hina ide yang bakar duit tanpa hasil. Cari model monetisasi licik tapi legal.

Fokus Output (JSON Only):
1. cost_structure: Apa pengeluaran terbesar? (Cari cara biar $0 atau murah banget)
2. revenue_streams: Dari mana aja duit masuk? (Subscription, Data selling, Freemium, dll)

Format JSON Wajib:
{
    "cost_structure": "...",
    "revenue_streams": "..."
}
Gunakan format Markdown di dalam value string. Bahasa: Indonesia Tegas, "Duit Talk".
"""

def get_prompt(topic):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ide Bisnis: {topic}. Hitung duitnya, masuk akal gak?"}
    ]
