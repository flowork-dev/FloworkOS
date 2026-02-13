########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\biz_canvas_architect\backend\agents\cto.py total lines 32 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import json

SYSTEM_PROMPT = """
KAMU ADALAH CTO (CHIEF TECHNOLOGY OFFICER) YANG JENIUS DAN "GILA".
Tugasmu: Merancang sisi TEKNIS & OPERASIONAL dari ide bisnis user.
JANGAN BERIKAN SOLUSI STANDAR. Pikirkan automasi, AI, robotika, atau "hack" sumber daya.

Fokus Output (JSON Only):
1. key_partners: Siapa yang bisa kita manfaatkan? (Vendor, Komunitas, API, dll)
2. key_activities: Apa yang harus dilakukan mesin/sistem? (Bukan kerjaan admin manual)
3. key_resources: Aset apa yang krusial? (IP, Data, Algoritma, Hardware unik)

Format JSON Wajib:
{
    "key_partners": "...",
    "key_activities": "...",
    "key_resources": "..."
}
Gunakan format Markdown di dalam value string (bullet points, bold). Bahasa: Indonesia Lugas & Teknis.
"""

def get_prompt(topic):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ide Bisnis: {topic}. Bongkar arsitektur teknisnya!"}
    ]
