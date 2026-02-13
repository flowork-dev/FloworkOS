########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_cli\cli.py total lines 32 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sys
import argparse
from .core.api_client import ApiClient
def main():

    parser = argparse.ArgumentParser(description="Flowork Command-Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    parser_status = subparsers.add_parser("status", help="Check the connection status to the Flowork API server.")
    args = parser.parse_args()
    print("--- Flowork CLI Initializing ---")
    api = ApiClient()
    if args.command == "status":
        print("Attempting to connect to Flowork server...")
        success, response = api.get_server_status()
        if success:
            server_status = response.get('status', 'unknown')
            kernel_version = response.get('version', 'N/A')
            print(f"✅ Connection successful!")
            print(f"   Server Status: {server_status}")
            print(f"   Kernel Version: {kernel_version}")
        else:
            print(f"❌ Connection failed: {response}")
            sys.exit(1)
    else:
        print("No command provided. Use 'status' to check server connection.")
        print("Example: poetry run python -m flowork_cli status")
