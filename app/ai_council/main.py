########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\main.py total lines 507 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import requests
import sqlite3
import logging
import re
import html
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agents import load_all_agents
except ImportError:
    class MockAgent:
        def __init__(self, d): self.__dict__.update(d)
        def get_prompt_instruction(self): return ""
        def get_profile(self): return {"name": self.name, "role": self.role, "icon": self.icon, "color": self.color, "border": self.border}

    def load_all_agents():
        return [
            MockAgent({"name": "DeepSeek Strategist", "role": "Strategi", "icon": "mdi-chess-knight", "color": "text-purple-400", "border": "border-purple-500"}),
            MockAgent({"name": "Gemini Analyst", "role": "Fakta Data", "icon": "mdi-chart-line-variant", "color": "text-blue-400", "border": "border-blue-500"}),
            MockAgent({"name": "ChatGPT Critic", "role": "Kritikus", "icon": "mdi-gavel", "color": "text-green-400", "border": "border-green-500"})
        ]

logger = logging.getLogger("Node.AI_Council")
logger.setLevel(logging.INFO)

MAX_ROUNDS = 30
DB_PATH = os.path.join(os.getcwd(), "council_history.db")

def _trigger_neural_indexing(user_id, topic, content):
    """
    Helper untuk memasukkan hasil rapat ke Neural Vault secara otomatis.
    Metode: Direct DB Access (Sesuai pola inject_god_mode_secrets).
    """
    db_path = "/app/data/flowork_core.db"
    if not os.path.exists(db_path):
        db_path = "C:\\FLOWORK\\data\\flowork_core.db"

    if not os.path.exists(db_path):
        logger.warning("⚠️ [Neural Indexer] Core DB not found, skipping indexing.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now = time.time()

        source = f"AI Council: {topic[:30]}..."
        tags = json.dumps({"app": "ai_council", "type": "final_verdict"})

        cursor.execute("""
            INSERT INTO NeuralKnowledge (user_id, content, source, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, content, source, tags, now, now))

        knowledge_id = cursor.lastrowid


        conn.commit()
        conn.close()
        logger.info(f"🧠 [Neural Indexer] Successfully indexed verdict to Vault (ID: {knowledge_id})")
    except Exception as e:
        logger.error(f"❌ [Neural Indexer] Failed to index: {e}")


def init_history_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (job_id TEXT PRIMARY KEY, title TEXT, created_at TIMESTAMP, last_updated TIMESTAMP)''')
        conn.commit(); conn.close()
    except Exception as e: logger.error(f"DB Init Error: {e}")
init_history_db()

def save_session_metadata(job_id, title):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor(); now = datetime.now().isoformat()
        cursor.execute("SELECT title FROM sessions WHERE job_id = ?", (job_id,))
        if cursor.fetchone(): cursor.execute("UPDATE sessions SET last_updated = ? WHERE job_id = ?", (now, job_id))
        else:
            cursor.execute("INSERT INTO sessions (job_id, title, created_at, last_updated) VALUES (?, ?, ?, ?)", (job_id, title[:50], now, now))
        conn.commit(); conn.close()
    except Exception as e: logger.error(f"DB Save Error: {e}")

def get_all_sessions():
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("SELECT job_id, title, created_at FROM sessions ORDER BY last_updated DESC")
        rows = cursor.fetchall(); conn.close()
        return [{"job_id": r[0], "title": r[1], "date": r[2]} for r in rows]
    except: return []

def rename_session_in_db(job_id, new_title):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET title = ?, last_updated = ? WHERE job_id = ?", (new_title, datetime.now().isoformat(), job_id))
        conn.commit(); conn.close(); return True
    except: return False

def delete_session_from_db(job_id):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE job_id = ?", (job_id,))
        conn.commit(); conn.close()
        if os.path.exists(get_state_file(job_id)): os.remove(get_state_file(job_id))
        return True
    except: return False

def inject_god_mode_secrets():
    target_vars = ["GEMINI_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]
    db_path = "/app/data/flowork_core.db"
    if not os.path.exists(db_path):
        db_path = "C:\\FLOWORK\\data\\flowork_core.db" # Fallback Windows
    if not os.path.exists(db_path): return
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor(); cursor.execute("PRAGMA table_info(variables)")
        cols = [c[1] for c in cursor.fetchall()]
        key_col = next((x for x in ["name", "key", "variable_name"] if x in cols), None)
        val_col = "value" if "value" in cols else "val"
        if key_col:
            for key in target_vars:
                if os.getenv(key): continue
                try:
                    cursor.execute(f"SELECT {val_col} FROM variables WHERE {key_col} = ? LIMIT 1", (key,))
                    row = cursor.fetchone()
                    if row and row[0]: os.environ[key] = str(row[0])
                except: pass
        conn.close()
    except: pass
inject_god_mode_secrets()

def get_state_file(job_id): return os.path.join(os.getcwd(), f"state_{job_id}.json")
def _save_result(job_id, data):
    try:
        with open(get_state_file(job_id) + ".tmp", "w") as f: json.dump(data, f)
        os.replace(get_state_file(job_id) + ".tmp", get_state_file(job_id))
    except Exception as e: logger.error(f"⚠️ Save Error: {e}")

def clean_and_repair_text(text):
    if not text: return ""
    text = html.unescape(text)
    text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def _query_openai_native(api_key, model, prompt_text):
    if not api_key: return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.7,
        "max_tokens": 1500 # Increased for better reasoning
    }
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            return clean_and_repair_text(r.json()['choices'][0]['message']['content'])
    except: pass
    return None

def _query_deepseek_native(api_key, prompt_text):
    if not api_key: return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    try:
        r = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            return clean_and_repair_text(r.json()['choices'][0]['message']['content'])
    except: pass
    return None

CACHED_GEMINI_MODEL = None
def _find_gemini_model(api_key):
    global CACHED_GEMINI_MODEL
    if CACHED_GEMINI_MODEL: return CACHED_GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = r.json().get('models', [])
            priorities = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
            for p in priorities:
                for m in models:
                    if p in m.get('name', '') and 'generateContent' in m.get('supportedGenerationMethods', []):
                        CACHED_GEMINI_MODEL = m.get('name', '').replace("models/", "")
                        return CACHED_GEMINI_MODEL
            if models: return models[0].get('name', '').replace("models/", "")
    except: pass
    return "gemini-1.5-flash"

def _query_gemini_native(api_key, prompt_text, attachment=None):
    if not api_key: return None
    model = _find_gemini_model(api_key)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    parts = [{"text": prompt_text}]
    if attachment: parts.append({"inline_data": {"mime_type": attachment['mime'], "data": attachment['data']}})

    try:
        r = requests.post(url, json={"contents": [{"parts": parts}]}, timeout=60)
        if r.status_code == 200:
            return clean_and_repair_text(r.json()['candidates'][0]['content']['parts'][0]['text'])
        if r.status_code == 429: return "QUOTA_HABIS" # Signal specifically for failover
    except: pass
    return None

def _query_smart_router(priority_list, prompt_text, attachment=None):
    """
    Mencoba provider satu per satu sesuai prioritas.
    Jika satu gagal/quota habis, lanjut ke yang berikutnya.
    """
    errors = []

    for provider in priority_list:
        res = None
        try:
            if provider == "openai":
                res = _query_openai_native(os.getenv("OPENAI_API_KEY"), "gpt-4o-mini", prompt_text)
            elif provider == "deepseek":
                res = _query_deepseek_native(os.getenv("DEEPSEEK_API_KEY"), prompt_text)
            elif provider == "gemini":
                res = _query_gemini_native(os.getenv("GEMINI_API_KEY"), prompt_text, attachment)
        except Exception as e:
            errors.append(f"{provider}: {str(e)}")
            continue

        if res == "QUOTA_HABIS":
            errors.append(f"{provider}: Quota Exceeded")
            continue # Lanjut ke next provider

        if res:
            return res # Success!

    return f"ERROR_FAIL: {'; '.join(errors)}"

def _query_debater(agent, topic, context_history, attachment=None, template=None, previous_context=None):
    custom_instruction = getattr(agent, 'custom_prompt_session', "")
    base_instruction = agent.get_prompt_instruction() if hasattr(agent, 'get_prompt_instruction') else ""
    final_template = template if template and len(template) > 50 else DEFAULT_DEBATER

    focus_instruction = ""
    if previous_context:
        focus_instruction = f"\n\n👉 FOKUS UTAMA ANDA: Tanggapi '{previous_context['speaker']}' yang baru saja berkata: \"{previous_context['content'][:200]}...\"\nANDA HARUS MENYEBUT NAMANYA DAN MELANJUTKAN/MENDEBAT ARGUMENNYA. JANGAN MONOLOG."

    try:
        prompt_text = final_template.replace("{agent_name}", str(agent.name))\
                                    .replace("{agent_role}", str(agent.role))\
                                    .replace("{custom_instruction}", str(custom_instruction or base_instruction))\
                                    .replace("{topic}", str(topic))\
                                    .replace("{context_history}", str(context_history))
        prompt_text += focus_instruction
    except: prompt_text = DEFAULT_DEBATER

    agent_name_lower = agent.name.lower()
    priority = ["gemini", "deepseek", "openai"]
    if "chatgpt" in agent_name_lower or "gpt" in agent_name_lower:
        priority = ["openai", "deepseek", "gemini"]
    elif "deepseek" in agent_name_lower:
        priority = ["deepseek", "gemini", "openai"]
    elif "gemini" in agent_name_lower:
        priority = ["gemini", "deepseek", "openai"]

    return _query_smart_router(priority, prompt_text, attachment)

def _query_consensus_judge(judge, history, template=None):
    tpl = template if template and len(template) > 20 else DEFAULT_CONSENSUS
    try: prompt = tpl.replace("{judge_name}", str(judge.name)).replace("{context_history}", str(history))
    except: prompt = DEFAULT_CONSENSUS

    res = _query_smart_router(["gemini", "deepseek", "openai"], prompt)
    try:
        clean_json = res.replace("```json", "").replace("```", "").strip()
        if "ERROR_FAIL" in clean_json: return {"decision": "LANJUT", "reason": "Menunggu perbaikan koneksi..."}
        return json.loads(clean_json)
    except:
        if "SEPAKAT" in res.upper(): return {"decision": "SEPAKAT", "reason": "Decision inferred from text."}
        return {"decision": "LANJUT", "reason": "Analisis berlanjut..."}

def _query_final_verdict(judge, topic, history, template=None):
    tpl = template if template and len(template) > 20 else DEFAULT_VERDICT
    final_prompt = tpl.replace("{judge_name}", str(judge.name))\
                                  .replace("{topic}", str(topic))\
                                  .replace("{context_history}", str(history))
    return _query_smart_router(["gemini", "deepseek", "openai"], final_prompt)

def _query_clarification_judge(judge, topic):
    prompt = DEFAULT_CLARIFICATION.replace("{topic}", str(topic))
    res = _query_smart_router(["gemini", "deepseek", "openai"], prompt)
    try:
        clean_json = res.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        if len(str(topic)) < 15: return {"status": "AMBIGU", "message": "Topik terlalu singkat. Mohon jelaskan detailnya."}
        return {"status": "CLEAR", "message": ""}

DEFAULT_DEBATER = """Identitas: {agent_name} | Role: {agent_role}.
INSTRUKSI SPESIFIK: {custom_instruction}
DATA USER: '{topic}'
RIWAYAT: {context_history}
TUGAS:
1. JANGAN PAKE HTML ENTITIES (&quot;). Pake kutip biasa.
2. Jawab sebagai expert.
Output Max 1000 kata.
7. JIKA TOPIK USER TIDAK JELAS/SAMPAH (misal: 'test', 'halo' doang), LANGSUNG JAWAB: [STOP: AMBIGU] Alasan singkat..."""

DEFAULT_CONSENSUS = """HAKIM AGUNG: {judge_name}.
TUGAS: Cek apakah diskusi SUDAH CUKUP untuk mengambil keputusan final (Consensus)?
RIWAYAT: {context_history}
ATURAN JUDGEMENT:
1. Jika para agent sudah memberikan solusi konkrit dan saling setuju -> KEPUTUSAN: "SEPAKAT".
2. Jika ada agent yang berkata "Saya setuju", "Solusi ini sudah lengkap" -> KEPUTUSAN: "SEPAKAT".
3. Jika masih debat keras -> KEPUTUSAN: "LANJUT".
OUTPUT JSON: { "decision": "SEPAKAT" atau "LANJUT", "reason": "Alasan singkat..." }"""

DEFAULT_VERDICT = """PERAN: Hakim Agung AI Council.\nKONTEKS: User dalam kondisi KRITIS/PENTING (lihat history diskusi).\nTUGAS: Rangkum debat agent menjadi SATU SOLUSI KONKRET & EMPATIK.\n\nLARANGAN KERAS:\n1. JANGAN gunakan format surat pengadilan (Nomor Putusan, Penggugat, dll).\n2. JANGAN pakai [text placeholder]. Isi langsung solusinya.\n\nFORMAT OUTPUT (Markdown):\n# 🛡️ PUTUSAN FINAL: [JUDUL STRATEGI]\n\n### 1. 💌 PESAN DARI KAMI (EMPATHY)\n(Responlah curhatan user dengan sangat manusiawi, kuatkan mentalnya, sapa dia sebagai 'Commander' atau 'Bro').\n\n### 2. ⚔️ STRATEGI PEMUNGKAS (COMBINED AGENTS)\n(Gabungkan ide terbaik dari Debater).\n\n### 3. 🗺️ ROADMAP EKSEKUSI (STEP BY STEP)\n(Berikan langkah nyata 1-2 minggu ke depan).\n\n### 4. 🔮 TITAH TERAKHIR\n(Kalimat penutup yang membakar semangat).\n\nDATA:\nTopik: {topic}\nHistory: {context_history}"""

DEFAULT_CLARIFICATION = """ROLE: Hakim Agung.\nTUGAS: Analisis apakah input user ini JELAS untuk diperdebatkan atau AMBIGU/SAMPAH?\nINPUT USER: "{topic}"\n\nKRITERIA AMBIGU (STATUS: AMBIGU):\n1. Kata tunggal tidak bermakna: "test", "cek", "halo".\n2. Sapaan kosong.\n3. Random typing: "asdf".\n\nOUTPUT JSON: { "status": "CLEAR" atau "AMBIGU", "message": "Jika ambigu, tegur user dengan tegas." }"""

def handle_like_message(params):
    job_id = params.get("job_id"); idx = params.get("index")
    if not job_id or idx is None: return {"status": "error"}
    fpath = get_state_file(job_id)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r") as f: data = json.load(f)
            if "messages" in data and len(data["messages"]) > idx:
                data["messages"][idx]["liked"] = not data["messages"][idx].get("liked", False)
                _save_result(job_id, data)
                return {"status": "success", "liked": data["messages"][idx]["liked"]}
        except: pass
    return {"status": "error"}

def handle_stop_meeting(params):
    job_id = params.get("job_id")
    fpath = get_state_file(job_id)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r") as f: data = json.load(f)
            data["status"] = "stopped"
            _save_result(job_id, data)
            return {"status": "success"}
        except: pass
    return {"status": "error"}

def get_available_agents():
    try:
        agents = load_all_agents()
        return {"status": "success", "agents": [{"id": a.__class__.__name__, "profile": a.get_profile(), "default_prompt": a.get_prompt_instruction() if hasattr(a, 'get_prompt_instruction') else ""} for a in agents]}
    except: return {"status": "error"}

def run(payload):
    action = payload.get("action"); params = payload.get("params", {})
    user_id = payload.get("user_id", "public") # Added user_id pass through
    if action == "get_agents": return get_available_agents()
    if action == "start_meeting": return run_council(params, user_id)
    if action == "like_message": return handle_like_message(params)
    if action == "stop_meeting": return handle_stop_meeting(params)
    if action == "check":
        if os.path.exists(get_state_file(params.get("job_id"))):
            with open(get_state_file(params.get("job_id")), "r") as f: return json.load(f)
        return {"status": "running", "messages": []}
    if action == "get_history": return {"status": "success", "history": get_all_sessions()}
    if action == "rename_history": return {"status": "success"} if rename_session_in_db(params.get("job_id"), params.get("title")) else {"status": "error"}
    if action == "delete_history": return {"status": "success"} if delete_session_from_db(params.get("job_id")) else {"status": "error"}
    return {"status": "error"}

def run_council(params, user_id="public"):
    topic = params.get("topic"); job_id = params.get("job_id")
    agent_config = params.get("agent_config", {}); sys_prompts = params.get("system_prompts", {})
    files = params.get("files", []); active_attachment = files[0] if files else None

    messages = []
    existing_file = get_state_file(job_id)
    is_continuation = False

    if os.path.exists(existing_file):
        try:
            with open(existing_file, "r") as f:
                old = json.load(f)
                messages = old.get("messages", [])
                is_continuation = True
                old["status"] = "running"
                _save_result(job_id, old)
        except: pass

    save_session_metadata(job_id, topic)

    if topic:
        should_add = True
        if is_continuation and messages:
            if messages[-1].get('agent') == 'User' and messages[-1].get('content') == topic: should_add = False
        if should_add:
            u = topic
            if active_attachment: u += f"\n\n*[📎 {active_attachment.get('name')}]*"
            messages.append({"agent": "User", "role": "Commander", "content": u, "icon": "mdi-account-cowboy-hat", "time": time.strftime("%H:%M:%S")})
            _save_result(job_id, {"status": "running", "topic": topic, "messages": messages})

    active_debaters, judge = [], None
    try:
        for a in load_all_agents():
            aid = a.__class__.__name__; conf = agent_config.get(aid, {}); role = conf.get("role", "DEBATER")
            a.custom_prompt_session = conf.get("prompt")
            if role == "JUDGE": judge = a; a.role = "HAKIM AGUNG"; a.border="border-yellow-500"; a.color="text-yellow-400"
            elif role == "MODERATOR": a.role = "MODERATOR"; a.border="border-teal-500"; a.color="text-teal-400"; active_debaters.insert(0, a)
            elif role != "OFF": active_debaters.append(a)
    except: return

    if not judge:
        class SysJudge: name="Auto-Judge"; role="HAKIM"; icon="mdi-gavel"; color="text-yellow-400"; border="border-yellow-500"
        judge = SysJudge()

    if not is_continuation or (len(messages) < 5):
        clarification = _query_clarification_judge(judge, topic)
        if clarification.get("status") == "AMBIGU":
            msg = clarification.get("message", "Mohon perjelas topik Anda.")
            messages.append({"agent": judge.name, "role": "HAKIM AGUNG", "content": f"✋ **INTERUPSI:** {msg}", "icon": judge.icon, "color": judge.color, "border": judge.border, "time": time.strftime("%H:%M:%S")})
            _save_result(job_id, {"status": "stopped", "messages": messages})
            return {"status": "success"}

    for i in range(MAX_ROUNDS):
        if os.path.exists(existing_file):
             with open(existing_file, 'r') as f:
                 if json.load(f).get("status") == "stopped": return

        valid_debates_count = 0
        for agent in active_debaters:
            if os.path.exists(existing_file):
                 with open(existing_file, 'r') as f:
                     if json.load(f).get("status") == "stopped": return

            previous_context = None
            if len(messages) > 0:
                last_msg = messages[-1]
                if last_msg.get('role') != 'ALERT':
                    previous_context = {"speaker": last_msg['agent'], "content": last_msg['content']}

            mission_msg = messages[0]['content'] if messages else "No Mission Context Found"
            last_verdict = next((m['content'] for m in reversed(messages) if "PUTUSAN FINAL" in m['content']), "Belum ada putusan sebelumnya.")

            pinned_context = f"📌 [MISSION CRITICAL - JANGAN LUPAKAN INI]:\n{mission_msg}\n\n🏆 [HASIL PUTUSAN TERAKHIR]:\n{last_verdict}\n\n"
            recent_context = "\n".join([f"{m['agent']}: {m['content']}" for m in messages[-30:]])
            full_context = pinned_context + recent_context

            resp = _query_debater(agent, topic, full_context, active_attachment, sys_prompts.get("debater_main"), previous_context)

            if os.path.exists(existing_file):
                 with open(existing_file, 'r') as f:
                     check_status = json.load(f)
                     if check_status.get("status") == "stopped": return

            if "ERROR_FAIL" in resp:
                err_msg = f"⚠️ {agent.name} GAGAL MERESPON: {resp}"
                messages.append({"agent": "SYSTEM", "role": "ALERT", "content": err_msg, "icon": "mdi-alert-circle", "color": "text-red-500", "time": time.strftime("%H:%M:%S")})
                _save_result(job_id, {"status": "running", "messages": messages})
            elif "[STOP: AMBIGU]" in resp:
                reason = resp.replace("[STOP: AMBIGU]", "").strip()
                messages.append({"agent": agent.name, "role": "INTERRUPT", "content": f"🛑 **DEBAT DIBATALKAN:** {reason}", "icon": agent.icon, "color": "text-red-500", "border": "border-red-500", "time": time.strftime("%H:%M:%S")})
                _save_result(job_id, {"status": "stopped", "messages": messages})
                return
            else:
                messages.append({"agent": agent.name, "role": agent.role, "content": resp, "icon": agent.icon, "color": agent.color, "border": agent.border, "time": time.strftime("%H:%M:%S")})
                _save_result(job_id, {"status": "running", "messages": messages})
                valid_debates_count += 1
            time.sleep(2)

        if valid_debates_count > 0:
            if os.path.exists(existing_file):
                 with open(existing_file, 'r') as f:
                     if json.load(f).get("status") == "stopped": return

            judge_context = pinned_context + "\n".join([f"{m['agent']}: {m['content']}" for m in messages[-20:]])
            v = _query_consensus_judge(judge, judge_context, sys_prompts.get("consensus_logic"))
            if v.get("decision") == "SEPAKAT":
                fin = _query_final_verdict(judge, topic, judge_context, sys_prompts.get("final_verdict"))
                messages.append({"agent": judge.name, "role": "HAKIM AGUNG", "content": fin, "icon": judge.icon, "color": judge.color, "border": judge.border, "time": time.strftime("%H:%M:%S")})
                _save_result(job_id, {"status": "success", "messages": messages})

                _trigger_neural_indexing(user_id, topic, fin)

                break
            else:
                 messages.append({"agent": judge.name, "role": judge.role, "content": f"**STATUS: {v.get('decision')}**\n_{v.get('reason')}_", "icon": judge.icon, "color": judge.color, "border": judge.border, "time": time.strftime("%H:%M:%S")})
                 _save_result(job_id, {"status": "running", "messages": messages})
        time.sleep(1)

    if os.path.exists(existing_file):
        with open(existing_file, 'r') as f:
            if json.load(f).get("status") != "stopped":
                _save_result(job_id, {"status": "success", "messages": messages})
    return {"status": "success"}
