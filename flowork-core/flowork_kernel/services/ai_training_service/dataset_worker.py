########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\dataset_worker.py total lines 148 
########################################################################

import os
import re
import json
import time

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PyPDF2 = None
    PDF_SUPPORT = False
    print("[DatasetWorker] ⚠️ PyPDF2 missing. PDF support disabled.")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    docx = None
    DOCX_SUPPORT = False
    print("[DatasetWorker] ⚠️ python-docx missing. DOCX support disabled.")

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

class DatasetWorker:
    def __init__(self, data_path):
        self.data_path = data_path

    def _sanitize_text(self, text):
        if not text or not isinstance(text, str): return text
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]', text)
        text = re.sub(r'\b(\+?\d{1,3}[- ]?)?\d{8,13}\b', '[REDACTED_PHONE]', text)
        return text

    def _process_raw_content(self, file_path):
        content = ""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                if PDF_SUPPORT and PyPDF2:
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        if reader.is_encrypted:
                            try: reader.decrypt("")
                            except: return "ERROR: PDF is encrypted."

                        for page in reader.pages:
                            extracted = page.extract_text()
                            if extracted: content += extracted + "\n"
                else:
                    return "ERROR: PDF Library (PyPDF2) not installed on server."

            elif (ext == '.docx' or ext == '.doc'):
                if DOCX_SUPPORT and docx:
                    doc = docx.Document(file_path)
                    for para in doc.paragraphs:
                        content += para.text + "\n"
                else:
                    return "ERROR: Word Library (python-docx) not installed on server."

            elif ext in ['.txt', '.md', '.log', '.py', '.js', '.json', '.csv']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

            elif ext == '.html' and BeautifulSoup:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    content = soup.get_text(separator=' ')
            else:
                return None
        except Exception as e:
            print(f"[DatasetWorker] Error processing {file_path}: {e}")
            return None

        return self._sanitize_text(content)

    def save_uploaded_dataset(self, filename, content_bytes):
        try:
            upload_dir = os.path.join(self.data_path, "uploads")
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)

            safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ','.','_','-')]).strip()

            if not safe_name:
                safe_name = f"upload_{int(time.time())}.bin"

            file_path = os.path.join(upload_dir, safe_name)

            with open(file_path, "wb") as f:
                f.write(content_bytes)

            print(f"[DatasetWorker] Saved: {file_path}")
            return safe_name
        except Exception as e:
            print(f"[DatasetWorker] Upload Save Failed: {e}")
            raise e

    def load_dataset_from_file(self, dataset_name):
        dataset_name = os.path.basename(dataset_name)

        possible_path = os.path.join(self.data_path, "uploads", dataset_name)
        if not os.path.exists(possible_path) and not os.path.isabs(dataset_name):
                possible_path = os.path.join(self.data_path, "datasets", dataset_name)

        if os.path.exists(possible_path):
            ext = os.path.splitext(possible_path)[1].lower()
            dataset_data = []

            if ext == '.json':
                try:
                    with open(possible_path, 'r', encoding='utf-8') as f:
                        raw_json = json.load(f)
                        if isinstance(raw_json, list): return raw_json
                except: pass

            raw_text = self._process_raw_content(possible_path)

            if raw_text and "ERROR:" not in raw_text[:20]:
                if raw_text.count('\n\n') > 5: chunks = raw_text.split('\n\n')
                else: chunks = raw_text.split('\n')

                for chunk in chunks:
                    cleaned = chunk.strip()
                    if len(cleaned) > 5:
                        dataset_data.append({"prompt": "Analyze the following:", "response": cleaned})

                if not dataset_data and len(raw_text.strip()) > 0:
                     dataset_data.append({"prompt": "Analyze the document:", "response": raw_text.strip()})

                return dataset_data

            elif raw_text and "ERROR:" in raw_text:
                print(f"[DatasetWorker] Processing Error: {raw_text}")

        else:
            print(f"[DatasetWorker] File not found: {possible_path}")

        return None
