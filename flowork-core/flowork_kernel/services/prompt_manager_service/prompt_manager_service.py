########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\prompt_manager_service\prompt_manager_service.py total lines 141 
########################################################################

import uuid
import sqlite3
from ..base_service import BaseService

class PromptManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self._init_db()
        self.logger.info("PromptManagerService Initialized.")

    def _init_db(self):
        """Ensures the prompt_templates table exists."""
        try:
            conn = self._get_db_connection()
            if not conn:
                return

            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_templates (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
             self.logger.error(f"PromptManagerService(init_db): Error - {e}")

    def _get_db_connection(self):
        """Helper to get DB connection from the main DatabaseService."""
        db_service = self.kernel.get_service("database_service")
        if not db_service:
            self.logger.critical("PromptManagerService CRITICAL: DatabaseService is not available.")
            return None
        return db_service.get_connection()

    def get_all_prompts(self):
        try:
            conn = self._get_db_connection()
            if not conn: return []

            with conn:
                conn.row_factory = self._dict_factory
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, content FROM prompt_templates ORDER BY name ASC")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"PromptManagerService(get_all_prompts): Error - {e}")
            return []

    def get_prompt(self, prompt_id: str):
        try:
            conn = self._get_db_connection()
            if not conn: return None

            with conn:
                conn.row_factory = self._dict_factory
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM prompt_templates WHERE id = ?", (prompt_id,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"PromptManagerService(get_prompt): Error - {e}")
            return None

    def create_prompt(self, prompt_data: dict):
        name = prompt_data.get('name')
        content = prompt_data.get('content')
        if not name or not content:
            return {'error': 'Name and content are required'}

        new_id = str(uuid.uuid4())
        try:
            conn = self._get_db_connection()
            if not conn: return {'error': 'DatabaseService not available'}

            with conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO prompt_templates (id, name, content) VALUES (?, ?, ?)", (new_id, name, content))
                conn.commit()
            return {'id': new_id, 'name': name, 'content': content, 'status': 'created'}
        except sqlite3.IntegrityError:
            return {'error': f"A prompt with the name '{name}' already exists."}
        except Exception as e:
            self.logger.error(f"PromptManagerService(create_prompt): Error - {e}")
            return {'error': str(e)}

    def update_prompt(self, prompt_id: str, prompt_data: dict):
        name = prompt_data.get('name')
        content = prompt_data.get('content')
        if not name or content is None:
            return {'error': 'Name and content are required'}

        try:
            conn = self._get_db_connection()
            if not conn: return {'error': 'DatabaseService not available'}

            with conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE prompt_templates SET name = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (name, content, prompt_id))
                if cursor.rowcount == 0:
                    return {'error': 'Prompt not found'}
                conn.commit()
            return {'id': prompt_id, 'name': name, 'content': content, 'status': 'updated'}
        except sqlite3.IntegrityError:
            return {'error': f"A prompt with the name '{name}' already exists."}
        except Exception as e:
            self.logger.error(f"PromptManagerService(update_prompt): Error - {e}")
            return {'error': str(e)}

    def delete_prompt(self, prompt_id: str):
        try:
            conn = self._get_db_connection()
            if not conn: return {'error': 'DatabaseService not available'}

            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM prompt_templates WHERE id = ?", (prompt_id,))
                if cursor.rowcount == 0:
                    return {'error': 'Prompt not found'}
                conn.commit()
            return {'id': prompt_id, 'status': 'deleted'}
        except Exception as e:
            self.logger.error(f"PromptManagerService(delete_prompt): Error - {e}")
            return {'error': str(e)}

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
