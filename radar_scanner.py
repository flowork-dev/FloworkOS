########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\radar_scanner.py total lines 50 
########################################################################

import os

def scan_radar():
    root_paths = {
        "GATEWAY": r"C:\FLOWORK\flowork-gateway",
        "CORE": r"C:\FLOWORK\flowork-core"
    }

    ignored_folders = {
        '__pycache__', '.git', 'venv', 'node_modules',
        'data', 'logs', 'training', 'ai_models'
    }

    print("="*60)
    print("         FLOWORK PROJECT RADAR SCANNER V1.0")
    print("="*60)

    for label, path in root_paths.items():
        print(f"\n[SCANNING {label}] -> {path}")
        if not os.path.exists(path):
            print(f"!!! PATH NOT FOUND: {path}")
            continue

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ignored_folders and not d.startswith('.')]

            level = root.replace(path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            folder_name = os.path.basename(root)

            if folder_name:
                print(f"{indent}📂 {folder_name}/")

            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if f.endswith('.py') or f.endswith('.json') or f.endswith('.yml'):
                    print(f"{sub_indent}📄 {f}")

    print("\n" + "="*60)
    print("SCAN COMPLETE. PLEASE COPY THIS OUTPUT TO GEMINI.")
    print("="*60)

if __name__ == "__main__":
    scan_radar()
