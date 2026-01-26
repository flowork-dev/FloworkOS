########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\sbackup.py total lines 110 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import datetime

OUTPUT_FILENAME = "BACKUP_FOR_GEMINI.txt"
INPUT_LIST_FILENAME = "backup_list.txt"
def get_target_files():
    """
    Reads target file paths from an external text file.
    Ignores empty lines and comments (lines starting with #).
    """
    file_list = []
    if os.path.exists(INPUT_LIST_FILENAME):
        try:
            with open(INPUT_LIST_FILENAME, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith("#"):
                        clean_path = clean_line.replace('"', '').replace("'", "")
                        file_list.append(clean_path)
            print(f"[INFO] Loaded {len(file_list)} paths from {INPUT_LIST_FILENAME}")
        except Exception as e:
            print(f"[ERROR] Could not read {INPUT_LIST_FILENAME}: {e}")
    else:
        print(f"[WARNING] {INPUT_LIST_FILENAME} not found! Please create it and add file paths.")

    return file_list

def normalize_path(path):
    """
    Converts mixed slashes to the OS specific separator.
    Handles relative paths by assuming C:\FLOWORK as root if not absolute.
    """
    clean_path = path.replace('"', '').replace("'", "").strip()

    normalized = os.path.normpath(clean_path)

    if not os.path.isabs(normalized) and not normalized.startswith("C:"):
        normalized = os.path.abspath(normalized)

    return normalized

def create_backup():
    print("="*60)
    print(f"   FLOWORK BACKUP TOOL - READ ONLY MODE")
    print(f"   Timestamp: {datetime.datetime.now()}")
    print("="*60)

    target_files_dynamic = get_target_files()

    if not target_files_dynamic:
        print("NO FILES TO PROCESS. CHECK YOUR backup_list.txt")
        return

    success_count = 0
    fail_count = 0

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as outfile:
        outfile.write(f"FLOWORK SOURCE CODE DUMP\n")
        outfile.write(f"Generated on: {datetime.datetime.now()}\n")
        outfile.write("="*80 + "\n\n")

        for raw_path in target_files_dynamic:
            filepath = normalize_path(raw_path)

            print(f"[SCAN] Processing: {filepath} ...", end=" ")

            if os.path.exists(filepath) and os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as infile:
                        content = infile.read()

                    outfile.write(f"START_FILE: {filepath}\n")
                    outfile.write("-" * 80 + "\n")
                    outfile.write(content)
                    outfile.write("\n" + "-" * 80 + "\n")
                    outfile.write(f"END_FILE: {filepath}\n")
                    outfile.write("=" * 80 + "\n\n")

                    print("OK ✅")
                    success_count += 1
                except Exception as e:
                    print(f"ERROR ❌ ({e})")
                    outfile.write(f"START_FILE: {filepath}\n")
                    outfile.write(f"[ERROR READING FILE: {e}]\n")
                    outfile.write("=" * 80 + "\n\n")
                    fail_count += 1
            else:
                print("NOT FOUND ❌")
                outfile.write(f"START_FILE: {filepath}\n")
                outfile.write(f"[FILE NOT FOUND ON DISK]\n")
                outfile.write("=" * 80 + "\n\n")
                fail_count += 1

    print("="*60)
    print(f"DONE! Summary:")
    print(f"   - Success: {success_count}")
    print(f"   - Failed : {fail_count}")
    print(f"   - Output : {os.path.abspath(OUTPUT_FILENAME)}")
    print("="*60)
    print("Please send the generated TXT file to Gemini.")

if __name__ == "__main__":
    create_backup()
