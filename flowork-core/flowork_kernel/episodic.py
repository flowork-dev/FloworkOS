########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\episodic.py total lines 172 
########################################################################

import json
import os
from pathlib import Path
import re
import uuid
from typing import Dict, Any, Optional, List

class EpisodicStore:


    def __init__(self, base_path: str, namespace: str):
        self.base = Path(base_path).resolve()
        self.namespace = namespace
        ns = self._sanitize(namespace)

        self.kv_root = self.base / "episodic" / ns
        self.episodes_root = self.base / "episodes" / ns

        try:
            self.kv_root.mkdir(parents=True, exist_ok=True)
            self.episodes_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"ERROR: Could not create episodic storage directory: {e}")
            raise

    def _sanitize(self, name: str) -> str:
        return "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", "/")).replace("..",".")


    def _kv_file_for(self, key: str) -> Path:

        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string.")

        safe_key = self._sanitize(key.replace(os.path.sep, "_"))

        if len(safe_key) > 200:
            safe_key = safe_key[:200]

        return self.kv_root / f"{safe_key}.json"

    def write(self, key: str, data: dict):

        file_path = self._kv_file_for(key)
        tmp_path = file_path.with_suffix(".json.tmp")
        try:
            tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp_path, file_path)

        except IOError as e:
            print(f"ERROR: Failed to write to episodic store (key: {key}): {e}")
            raise
        except TypeError as e:
            print(f"ERROR: Data for episodic store (key: {key}) is not JSON serializable: {e}")
            raise

    def read(self, key: str) -> dict | None:

        file_path = self._kv_file_for(key)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except (IOError, json.JSONDecodeError) as e:
            print(f"ERROR: Failed to read from episodic store (key: {key}): {e}")
            return None

    def delete(self, key: str) -> bool:

        file_path = self._kv_file_for(key)
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return True
        except IOError as e:
            print(f"ERROR: Failed to delete from episodic store (key: {key}): {e}")
            return False


    def save_episode(self, payload: Dict[str, Any]) -> str:

        episode_id = payload.get("episode_id") or str(uuid.uuid4())
        payload["episode_id"] = episode_id

        file_path = self.episodes_root / f"{episode_id}.json"
        tmp_path = file_path.with_suffix(".json.tmp")

        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, file_path)
        return episode_id

    def load_episode(self, episode_id: str) -> Dict[str, Any]:

        file_path = self.episodes_root / f"{episode_id}.json"
        if not file_path.exists():
            raise FileNotFoundError("Episode not found")
        return json.loads(file_path.read_text(encoding="utf-8"))

    def list_episodes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:

        files = list(self.episodes_root.glob("*.json"))
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if limit is not None:
            files = files[: max(0, int(limit))]

        out: List[Dict[str, Any]] = []
        for p in files:
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

if __name__ == "__main__":
    import shutil

    TEST_BASE = "data/agents_test"
    TEST_NS = "test_tenant/test_agent_123"

    if Path(TEST_BASE).exists():
        shutil.rmtree(TEST_BASE)
        print(f"Cleaned up {TEST_BASE}")

    store = EpisodicStore(base_path=TEST_BASE, namespace=TEST_NS)
    print(f"Store KV Root: {store.kv_root}")
    print(f"Store Episodes Root: {store.episodes_root}")

    key1 = "mission_brief"
    data1 = {"goal": "Analyze flowork.cloud", "priority": 1}

    print(f"\nTesting R3 KV Write (key: {key1})...")
    store.write(key1, data1)

    print(f"Testing R3 KV Read (key: {key1})...")
    read_data1 = store.read(key1)
    print(f"Data: {read_data1}")
    assert read_data1 == data1

    print("R3 KV API compatibility: PASSED")

    print("\nTesting R4 Episode API (save_episode)...")
    ep1_data = {"title": "First Run", "step_count": 5}
    ep1_id = store.save_episode(ep1_data)
    print(f"Saved episode {ep1_id}")

    ep2_data = {"title": "Second Run", "step_count": 10}
    ep2_id = store.save_episode(ep2_data)
    print(f"Saved episode {ep2_id}")

    print(f"Testing R4 Episode API (load_episode: {ep1_id})...")
    loaded_ep1 = store.load_episode(ep1_id)
    print(f"Data: {loaded_ep1}")
    assert loaded_ep1["title"] == ep1_data["title"]

    print("Testing R4 Episode API (list_episodes)...")
    recent_episodes = store.list_episodes(limit=10)
    print(f"Found {len(recent_episodes)} episodes.")
    assert len(recent_episodes) == 2
    assert recent_episodes[0]["episode_id"] == ep2_id

    print("R4 Episode API: PASSED")

    shutil.rmtree(TEST_BASE)
    print(f"\nCleanup complete. Removed {TEST_BASE}")
