########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\modules\youtube_keyword_researcher\processor.py total lines 416 
########################################################################

import os
import sys
import json
import re
import uuid
import csv
import traceback
import subprocess
import datetime
import math
import importlib
import importlib.util
from collections import Counter
from flowork_kernel.api_contract import BaseModule, IExecutable

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(CURRENT_DIR, "vendor_libs")
MODELS_DIR = os.path.join(CURRENT_DIR, "models_cache")

if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

os.makedirs(VENDOR_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

print(f"--- [YouTubeResearcher] Persistent Storage Active ---", file=sys.stderr, flush=True)

def is_package_installed(package_name):
    try:
        return importlib.util.find_spec(package_name) is not None
    except:
        return False

def ensure_dependencies():
    requirements = {
        "yt-dlp": "yt_dlp",
        "faster-whisper": "faster_whisper"
    }

    missing = []
    for pip_name, import_name in requirements.items():
        if not is_package_installed(import_name):
            missing.append(pip_name)

    if missing:
        print(f"⚠️ [YouTubeResearcher] Missing Libs: {missing}. Installing...", file=sys.stderr, flush=True)
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "-t", VENDOR_DIR,
                "--no-cache-dir"
            ] + missing)
            importlib.invalidate_caches()
            print("✅ [YouTubeResearcher] Libs Installed!", file=sys.stderr, flush=True)
            return True
        except Exception as e:
            print(f"❌ [YouTubeResearcher] Install failed: {e}", file=sys.stderr, flush=True)
            return False
    else:
        return True

if ensure_dependencies():
    try:
        import yt_dlp
        from faster_whisper import WhisperModel
        DEPENDENCIES_OK = True
    except ImportError:
        DEPENDENCIES_OK = False
else:
    DEPENDENCIES_OK = False

STOPWORDS = {
    'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'this', 'it', 'that',
    'yang', 'dan', 'di', 'dari', 'ini', 'itu', 'untuk', 'dengan', 'adalah', 'ke', 'pada',
    'guys', 'halo', 'oke', 'nah', 'jadi', 'video', 'channel', 'subscribe', 'like', 'comment',
    'bisa', 'akan', 'atau', 'saya', 'kita', 'kalau', 'jika', 'sudah', 'tapi', 'ada'
}

class YouTubeKeywordResearcher(BaseModule, IExecutable):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.logger_service = services.get("logger")
        self.temp_dir = os.path.join(os.getcwd(), "temp_research_audio")
        if not os.path.exists(self.temp_dir):
            try: os.makedirs(self.temp_dir)
            except: pass

    def _clean_text(self, text):
        if not text: return []
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
        words = text.split()
        return [w for w in words if w not in STOPWORDS and len(w) > 2]

    def _sanitize_filename(self, filename):
        return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

    def _get_ydl_opts(self):
        return {
            'quiet': True,
            'extract_flat': False,
            'skip_download': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'cachedir': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
        }

    def _download_metadata(self, url):
        opts = self._get_ydl_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _download_audio(self, url):
        unique_id = uuid.uuid4().hex
        output_template = os.path.join(self.temp_dir, f'{unique_id}.%(ext)s')

        opts = self._get_ydl_opts()
        opts.update({
            'skip_download': False,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128', # Turunin dikit biar enteng
            }],
            'external_downloader': 'ffmpeg',
            'external_downloader_args': ['-t', '180'], # LIMIT 180 DETIK (3 MENIT)
            'outtmpl': output_template,
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
            return os.path.join(self.temp_dir, f'{unique_id}.mp3')

    def _calculate_seo_score(self, title, description, tags):
        score = 0
        if not title: return 0
        title_words = self._clean_text(title)
        desc_lower = description.lower() if description else ""
        matches = sum(1 for word in title_words if word in desc_lower)
        score += min(30, matches * 5)
        if tags:
            tag_count = len(tags)
            if 5 <= tag_count <= 20: score += 20
            elif tag_count < 5: score += 10
            else: score += 15
        if len(desc_lower) > 200: score += 20
        elif len(desc_lower) > 50: score += 10
        if 20 <= len(title) <= 70: score += 10
        if tags and len(tags) > 0:
            tag_text = " ".join(tags).lower()
            tag_matches = sum(1 for word in title_words if word in tag_text)
            if tag_matches > 0: score += 20
            else: score += 10
        return min(100, score)

    def _calculate_engagement_rate(self, views, likes, comments):
        if not views or views == 0: return 0.0
        interactions = (likes or 0) + (comments or 0)
        rate = (interactions / views) * 100
        return round(rate, 2)

    def _estimate_earnings(self, views):
        if not views: return {"low": "$0", "high": "$0"}
        low_est = (views / 1000) * 0.50
        high_est = (views / 1000) * 4.00
        return {
            "low": f"${low_est:,.2f}",
            "high": f"${high_est:,.2f}",
            "avg_raw": (low_est + high_est) / 2
        }

    def _check_monetization_status(self, channel_subscribers, is_verified, raw_meta):
        if is_verified: return "MONETIZED (Verified)"
        if raw_meta.get('availability') == 'premium_only': return "MONETIZED (Premium)"
        if channel_subscribers and channel_subscribers > 1000: return "Likely Monetized"
        return "Not Monetized (Subs < 1k)"

    def _calculate_video_velocity(self, views, upload_date_str):
        if not views or not upload_date_str: return "N/A"
        try:
            upload_dt = datetime.datetime.strptime(upload_date_str, '%Y%m%d')
            now = datetime.datetime.now()
            diff = now - upload_dt
            hours = diff.total_seconds() / 3600
            if hours < 1: hours = 1
            velocity = views / hours
            return f"{velocity:,.0f} v/h"
        except: return "N/A"

    def _save_to_csv(self, data, folder_path, filename):
        if not folder_path or not os.path.isdir(folder_path):
            folder_path = self.temp_dir
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        full_path = os.path.join(folder_path, filename)
        trans_data = data.get("transcript_data")

        hook_text = "N/A"
        preview_text = "N/A"
        hook_analysis = "N/A"

        if isinstance(trans_data, dict):
            hook_text = trans_data.get("hook_text", "")[:200]
            preview_text = trans_data.get("full_text", "")[:500]
            hook_analysis = trans_data.get("hook_analysis", "N/A")
        elif isinstance(trans_data, str):
             preview_text = trans_data

        csv_row = {
            "Video Title": data["meta"]["title"],
            "URL": data.get("source_url", ""),
            "Channel": data["channel_intel"]["name"],
            "Subscribers": data["channel_intel"]["subscribers"],
            "Monetization Status": data["financials"]["monetization_status"],
            "Est. Earnings (Low)": data["financials"]["est_earnings"]["low"],
            "Views": data["meta"]["views"],
            "Velocity": data["video_ballistics"]["velocity"],
            "Engagement Rate": f"{data['video_ballistics']['engagement_rate']}%",
            "SEO Score": data['video_ballistics']['seo_score'],
            "Top Keywords": ", ".join(data["seo_analysis"]["top_keywords"]),
            "Hook (First 30s)": hook_text,
            "Hook Analysis": hook_analysis,
            "Transcript Preview": preview_text
        }

        with open(full_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=csv_row.keys())
            writer.writeheader()
            writer.writerow(csv_row)
        return full_path

    def _extract_inputs_recursive(self, payload):
        found = {}
        if isinstance(payload, dict):
            for k, v in payload.items():
                if isinstance(v, (str, int, float, bool)) and k not in found:
                    found[k] = v
                elif isinstance(v, dict):
                    nested = self._extract_inputs_recursive(v)
                    found.update(nested)
        return found

    def execute(self, payload, config, status_updater, mode="EXECUTE", **kwargs):
        def update_ui(msg, status="RUNNING"):
            print(f"📢 [Researcher] {msg}", file=sys.stderr, flush=True)
            if status_updater:
                try: status_updater(msg, status)
                except: pass

        try:
            update_ui("🚀 Initializing Researcher (Turbo Mode)...", "STARTING")

            extracted_inputs = self._extract_inputs_recursive(payload)
            inputs = {**config, **extracted_inputs}

            if not DEPENDENCIES_OK:
                return self._error("Dependencies error.", update_ui)

            video_url = inputs.get("video_url") or inputs.get("url")
            mode_input = inputs.get("research_depth", "Flash (Metadata Only)")
            whisper_model = inputs.get("whisper_model", "base")
            lang_hint = inputs.get("language_hint", "en")
            output_folder = inputs.get("output_folder")

            if not video_url:
                return self._error("❌ Video URL is EMPTY!", update_ui)

            update_ui(f"🕵️ Scanning: {video_url} | Mode: {mode_input}")

            try:
                meta = self._download_metadata(video_url)
            except Exception as e:
                return self._error(f"❌ YouTube Download Failed: {str(e)}", update_ui)

            title = meta.get('title', 'Unknown Video')
            desc = meta.get('description', '')
            tags = meta.get('tags', [])
            views = meta.get('view_count', 0)

            seo_score = self._calculate_seo_score(title, desc, tags)
            engagement_rate = self._calculate_engagement_rate(views, meta.get('like_count', 0), meta.get('comment_count', 0))
            velocity = self._calculate_video_velocity(views, meta.get('upload_date', ''))
            est_earnings = self._estimate_earnings(views)
            monetization = self._check_monetization_status(meta.get('channel_follower_count', 0), meta.get('channel_is_verified', False), meta)

            result_data = {
                "source_url": video_url,
                "meta": {
                    "title": title, "views": views, "likes": meta.get('like_count', 0),
                    "comments": meta.get('comment_count', 0), "upload_date": meta.get('upload_date', ''),
                    "duration": meta.get('duration', 0), "original_tags": tags,
                    "thumbnail": meta.get('thumbnail', ''), "description_full": desc
                },
                "channel_intel": {
                    "name": meta.get('uploader', 'Unknown'), "url": meta.get('uploader_url', ''),
                    "subscribers": meta.get('channel_follower_count', 0),
                    "channel_tags": meta.get('channel_tags', [])
                },
                "video_ballistics": {
                    "seo_score": seo_score, "engagement_rate": engagement_rate, "velocity": velocity
                },
                "financials": {
                    "est_earnings": est_earnings, "monetization_status": monetization
                },
                "transcript_data": "Not requested"
            }

            text_corpus = f"{title} {desc} " + " ".join(tags) * 5

            if "deep" in str(mode_input).lower():
                update_ui("🧠 [Deep Mode] Initializing Neural Audio Processor...")
                audio_file = None
                try:
                    update_ui("✂️ Downloading First 3 Mins Only (Turbo)...")
                    audio_file = self._download_audio(video_url)

                    update_ui(f"🎙️ Transcribing ({whisper_model})...")

                    model = WhisperModel(
                        whisper_model,
                        device="cpu",
                        compute_type="int8",
                        download_root=MODELS_DIR
                    )

                    segments, info = model.transcribe(
                        audio_file,
                        language=lang_hint if lang_hint else None,
                        beam_size=1
                    )

                    full_text_segments = []
                    hook_text = ""
                    current_time = 0
                    for s in segments:
                        full_text_segments.append(s.text)
                        if current_time < 30:
                            hook_text += s.text + " "
                            current_time = s.end

                    full_text = " ".join(full_text_segments)

                    hook_analysis = "Neutral"
                    if any(w in hook_text.lower() for w in self._clean_text(title)):
                        hook_analysis = "STRONG (Title Keywords in Hook)"
                    else:
                        hook_analysis = "WEAK (No Keyword Match)"

                    result_data["transcript_data"] = {
                        "full_text": full_text + "\n\n[...Transcript Limited to 3 Mins for Speed...]",
                        "hook_text": hook_text.strip(),
                        "hook_analysis": hook_analysis,
                        "detected_language": info.language
                    }
                    text_corpus += f" {full_text}"
                    update_ui("✅ Neural Transcription Complete!")

                except Exception as e:
                    self.logger_service.error(f"Deep Analysis Error: {e}")
                    update_ui(f"⚠️ Transcript Failed: {str(e)}", "WARNING")
                    result_data["transcript_data"] = f"Error: {str(e)}"
                finally:
                    if audio_file and os.path.exists(audio_file):
                        try: os.remove(audio_file)
                        except: pass
            else:
                update_ui("⚡ Flash Mode Active (Skipping AI)...")

            clean_words = self._clean_text(text_corpus)
            word_counts = Counter(clean_words)
            top_keywords = [item[0] for item in word_counts.most_common(30)]

            result_data["seo_analysis"] = {
                "top_keywords": top_keywords,
                "density": dict(word_counts.most_common(15))
            }

            update_ui("💾 Saving Mission Report...")
            safe_title = self._sanitize_filename(title)
            csv_filename = f"Scout_{safe_title[:30]}_{uuid.uuid4().hex[:4]}.csv"

            saved_path = "SKIPPED"
            if output_folder:
                try:
                    saved_path = self._save_to_csv(result_data, output_folder, csv_filename)
                    update_ui(f"✨ Secured: {saved_path}", "SUCCESS")
                except: saved_path = "FAILED_TO_SAVE"

            return {
                "output_name": "success",
                "payload": {
                    "result_json": result_data,
                    "csv_path": saved_path
                }
            }

        except Exception as e:
            traceback.print_exc()
            return self._error(f"CRITICAL ERROR: {str(e)}", update_ui)

    def _error(self, msg, updater):
        if updater: updater(msg, "ERROR")
        return {"output_name": "error", "payload": {"error": msg}}
