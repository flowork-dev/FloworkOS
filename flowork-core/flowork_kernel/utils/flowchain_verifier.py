########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\utils\flowchain_verifier.py total lines 69 
########################################################################

import json
import hashlib
import os
from web3.auto import w3
from eth_account.messages import encode_defunct
def calculate_hash(file_path):

    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except IOError:
        return None
def verify_workflow_chain(workflow_directory):

    if not os.path.isdir(workflow_directory):
        print(f"[Verifier] Directory not found: {workflow_directory}")
        return False, f"Directory not found: {workflow_directory}"
    try:
        files = sorted(
            [f for f in os.listdir(workflow_directory) if f.endswith('.json') and f.startswith('v')],
            key=lambda f: int(f.split('_')[0][1:])
        )
    except FileNotFoundError:
        print(f"[Verifier] Directory not found during list: {workflow_directory}")
        return False, f"Directory not found: {workflow_directory}"
    except Exception as e:
        print(f"[Verifier] Failed to sort version files: {e}")
        return False, f"Failed to sort version files: {e}"
    if not files:
        print(f"[Verifier] No version files found in: {workflow_directory}")
        return True, "No versions found, chain is valid by default."
    previous_file_hash = None
    for i, filename in enumerate(files):
        file_path = os.path.join(workflow_directory, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            signature = data.get('signature')
            author_id = data.get('author_id')
            workflow_data = data.get('workflow_data')
            if not signature or not author_id or workflow_data is None:
                raise ValueError(f"File {filename} is corrupt: missing signature, author_id, or workflow_data")
            unsigned_data_block = {"workflow_data": workflow_data}
            message_to_verify = json.dumps(unsigned_data_block, sort_keys=True, separators=(',', ':'))
            encoded_message = encode_defunct(text=message_to_verify)
            recovered_address = w3.eth.account.recover_message(encoded_message, signature=signature)
            if recovered_address.lower() != author_id.lower():
                raise ValueError(f"Invalid signature in version {data.get('version', filename)}. Address mismatch.")
            if i == 0:
                if data.get('previous_hash') is not None:
                     raise ValueError(f"Chain broken at {filename}: First version file should have null previous_hash.")
            else:
                if data.get('previous_hash') != previous_file_hash:
                    raise ValueError(f"Chain broken at {filename}! Hash mismatch. Expected {previous_file_hash}, got {data.get('previous_hash')}")
            previous_file_hash = calculate_hash(file_path)
        except Exception as e:
            print(f"[Verifier] CRITICAL: Chain verification failed for {filename}: {e}")
            return False, f"Verification failed for {filename}: {e}"
    print(f"[Verifier] Workflow '{os.path.basename(workflow_directory)}' chain is valid and secure.")
    return True, "Chain verified."
