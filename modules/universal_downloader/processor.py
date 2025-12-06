########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\universal_downloader\processor.py total lines 170 
########################################################################

import os
import sys
import json
import traceback
import subprocess
from flowork_kernel.api_contract import BaseModule, IExecutable

print("--- [UniversalDownloader] Checking Dependencies... ---", file=sys.stderr)

def ensure_yt_dlp():
    try:
        import yt_dlp
        return True
    except ImportError:
        print("⚠️ [UniversalDownloader] yt-dlp missing. Attempting AUTO-INSTALL...", file=sys.stderr)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            print("✅ [UniversalDownloader] yt-dlp installed successfully!", file=sys.stderr)
            return True
        except Exception as e:
            print(f"❌ [UniversalDownloader] Auto-install failed: {e}", file=sys.stderr)
            return False

if ensure_yt_dlp():
    import yt_dlp
    YT_DLP_AVAILABLE = True
else:
    YT_DLP_AVAILABLE = False

class UniversalDownloader(BaseModule, IExecutable):

    TIER = "builder"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.logger = services.get("logger")

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):

        if mode == "SIMULATE":
            return {
                "payload": {
                    "data": {
                        "file_path": "/mock/path/video.mp4",
                        "meta": {"title": "Mock Video", "uploader": "Flowork"}
                    }
                },
                "output_name": "success"
            }

        if not YT_DLP_AVAILABLE:
            msg = "CRITICAL: 'yt-dlp' library missing and Auto-Install failed. Please check internet connection or permissions."
            status_updater(msg, "ERROR")
            return {"payload": {"data": {"error": msg}}, "output_name": "error"}


        url = config.get("url")
        out_folder = config.get("output_folder")
        format_mode = config.get("format_mode", "best")
        cookie_file = config.get("cookie_file")
        proxy_url = config.get("proxy_url")

        if not url:
            return self._error("No URL provided!", status_updater)

        if not out_folder or not os.path.exists(out_folder):
            try:
                os.makedirs(out_folder, exist_ok=True)
            except:
                return self._error(f"Output folder invalid: {out_folder}", status_updater)

        status_updater(f"🚀 Initializing Downloader for: {url}", "INFO")

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    status_updater(f"⬇️ Downloading: {d.get('_percent_str')} | Speed: {d.get('_speed_str')}", "INFO")
                except: pass
            elif d['status'] == 'finished':
                status_updater("✅ Download Complete. Processing/Muxing...", "INFO")

        ydl_opts = {
            'outtmpl': os.path.join(out_folder, '%(title)s [%(id)s].%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'restrictfilenames': True,
            'nocheckcertificate': True,
        }

        if format_mode == "audio_mp3":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif format_mode == "video_only":
            ydl_opts['format'] = 'bestvideo'
        elif format_mode == "worst":
            ydl_opts['format'] = 'worst'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'

        if cookie_file and os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        if proxy_url:
            ydl_opts['proxy'] = proxy_url

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'Unknown')
                uploader = info_dict.get('uploader', 'Unknown')
                duration = info_dict.get('duration', 0)

                status_updater(f"🎬 Found: {video_title} by {uploader}", "INFO")

                error_code = ydl.download([url])
                if error_code != 0:
                    raise Exception(f"yt-dlp exited with error code {error_code}")

                target_filename = ydl.prepare_filename(info_dict)
                if format_mode == "best" and config.get("format_mode") != "video_only":
                     base, _ = os.path.splitext(target_filename)
                     potential_path = base + ".mp4"
                     if os.path.exists(potential_path):
                         target_filename = potential_path
                elif format_mode == "audio_mp3":
                    base, _ = os.path.splitext(target_filename)
                    target_filename = base + ".mp3"

                if not os.path.exists(target_filename):
                    vid_id = info_dict.get('id')
                    for f in os.listdir(out_folder):
                        if vid_id in f:
                            target_filename = os.path.join(out_folder, f)
                            break

            status_updater("✅ All Done!", "SUCCESS")
            return {
                "payload": {
                    "data": {
                        "file_path": target_filename,
                        "meta": {
                            "title": video_title,
                            "uploader": uploader,
                            "duration": duration,
                            "source_url": url
                        }
                    }
                },
                "output_name": "success"
            }

        except Exception as e:
            traceback.print_exc()
            return self._error(f"Download Failed: {str(e)}", status_updater)

    def _error(self, msg, updater):
        updater(msg, "ERROR")
        return {"payload": {"data": {"error": msg}}, "output_name": "error"}
