########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\database_service.py total lines 397 
########################################################################

import os
import sqlite3
import logging
import json
import uuid
from contextlib import contextmanager
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton

DB_SCHEMA_VERSION = 7 # [PHASE 4] Bump version for App Storage

class DatabaseService(BaseService):
    def __init__(self, kernel, service_id, db_name="flowork_core.db"):
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.data_dir = self.kernel.data_path
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.db_path = os.path.join(self.data_dir, db_name)
        self.logger.info(f"DatabaseService initialized. DB Path: {self.db_path}")

        self.create_tables()

    def create_connection(self):
        """Creates a new connection to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create database connection: {e}", exc_info=True)
            return None

    def get_connection(self):
        """
        Alias for create_connection to maintain compatibility with services
        expecting get_connection() pattern.
        """
        return self.create_connection()

    @contextmanager
    def transaction(self):
        """
        Context manager untuk transaksi database yang aman.
        Otomatis commit jika sukses, otomatis rollback jika error,
        dan PASTI menutup koneksi di akhir.
        """
        conn = self.create_connection()
        if not conn:
            raise ConnectionError("Could not establish database connection.")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Transaction failed, changes rolled back: {e}")
            raise e
        finally:
            conn.close()

    def execute_app_query(self, app_id: str, query_type: str, collection: str, payload: dict):
        """
        Teller Bank: Melayani permintaan data dari App dengan validasi ketat.
        Mencegah App menyentuh tabel sensitif atau data App lain.
        """
        if collection.startswith("system_") or collection in ["users", "engines", "DBVersion"]:
             if query_type != "select":
                 raise PermissionError(f"⚠️ [IronBank] App {app_id} dilarang mengubah tabel sistem '{collection}'!")

        if collection == "app_storage":
            payload["owner_app_id"] = app_id

        try:
            return self._perform_db_operation(query_type, collection, payload)
        except Exception as e:
            self.logger.error(f"❌ [IronBank] Transaction failed for {app_id}: {e}")
            raise e

    def _perform_db_operation(self, query_type, collection, payload):
        """Helper internal untuk eksekusi CRUD sederhana."""
        with self.transaction() as conn:
            cursor = conn.cursor()

            if collection == "app_storage":
                table_name = "app_storage"

                if query_type == "insert":
                    key = payload.get("key", str(uuid.uuid4()))
                    val = json.dumps(payload.get("value", {}))
                    app_id = payload.get("owner_app_id")

                    cursor.execute(
                        f"INSERT OR REPLACE INTO {table_name} (key, owner_app_id, value) VALUES (?, ?, ?)",
                        (key, app_id, val)
                    )
                    return {"status": "success", "key": key}

                elif query_type == "select":
                    app_id = payload.get("owner_app_id")
                    key = payload.get("key")

                    if key:
                        cursor.execute(f"SELECT value FROM {table_name} WHERE owner_app_id=? AND key=?", (app_id, key))
                        row = cursor.fetchone()
                        return json.loads(row[0]) if row else None
                    else:
                        cursor.execute(f"SELECT key, value FROM {table_name} WHERE owner_app_id=?", (app_id,))
                        rows = cursor.fetchall()
                        return {r[0]: json.loads(r[1]) for r in rows}

                elif query_type == "delete":
                    app_id = payload.get("owner_app_id")
                    key = payload.get("key")
                    if key:
                        cursor.execute(f"DELETE FROM {table_name} WHERE owner_app_id=? AND key=?", (app_id, key))
                    return {"status": "deleted"}


            return {"status": "error", "message": "Unsupported collection or operation"}

    def create_tables(self):
        conn = self.create_connection()
        if not conn:
            self.logger.error("Cannot create tables. No DB connection.")
            return

        try:
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS DBVersion (
                id INTEGER PRIMARY KEY,
                version INTEGER NOT NULL
            )
            """)

            cursor.execute("SELECT version FROM DBVersion WHERE id = 1")
            row = cursor.fetchone()

            current_version = 0
            if row:
                current_version = row[0]
            else:
                cursor.execute("INSERT INTO DBVersion (id, version) VALUES (1, 0)")

            self.logger.info(f"Current DB schema version: {current_version}. Required version: {DB_SCHEMA_VERSION}")

            if current_version < 1:
                self.logger.info("Migrating schema to v1 (Initial)...")
                self._run_migration_v1(cursor)

            if current_version < 2:
                self.logger.info("Migrating schema to v2 (Add User/Auth tables)...")
                self._run_migration_v2(cursor)

            if current_version < 3:
                self.logger.info("Migrating schema to v3 (Add Jobs/Executions tables)...")
                self._run_migration_v3(cursor)

            if current_version < 4:
                self.logger.info("Migrating schema to v4 (Add user_id to Jobs)...")
                self._run_migration_v4(cursor)

            if current_version < 5:
                self.logger.info("Migrating schema to v5 (R5 - Add strategy to Executions)...")
                self._run_migration_v5(cursor)

            if current_version < 6:
                self.logger.info("Migrating schema to v6 (Add handles to Edges for routing)...")
                self._run_migration_v6(cursor)

            if current_version < 7:
                self.logger.info("Migrating schema to v7 (The Iron Bank - App Storage)...")
                self._run_migration_v7(cursor)

            cursor.execute("UPDATE DBVersion SET version = ? WHERE id = 1", (DB_SCHEMA_VERSION,))

            conn.commit()
            self.logger.info("Database tables verified/created successfully.")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to create/verify tables: {e}", exc_info=True)
            conn.rollback()
        finally:
            conn.close()

    def _run_migration_v1(self, cursor):
        """(V1) Initial tables for settings, variables, presets."""
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Variables (
            var_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT NOT NULL,
            value TEXT,
            is_secret INTEGER DEFAULT 0,
            is_enabled INTEGER DEFAULT 1,
            mode TEXT DEFAULT 'single',
            UNIQUE(user_id, name)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Presets (
            preset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            workflow_data TEXT,
            user_id TEXT,
            signature TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Datasets (
            name TEXT PRIMARY KEY,
            data TEXT
        )
        """)

    def _run_migration_v2(self, cursor):
        """(V2) Tables for Web3 Auth."""
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS engines (
            engine_id TEXT PRIMARY KEY,
            user_address TEXT NOT NULL,
            engine_token_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS engine_shares (
            share_id TEXT PRIMARY KEY,
            engine_id TEXT NOT NULL,
            user_address TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engine_id) REFERENCES engines (engine_id) ON DELETE CASCADE
        )
        """)

    def _run_migration_v3(self, cursor):
        """(V3) Tables for Job Queue."""
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Workflows (
            workflow_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Nodes (
            node_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            node_type TEXT NOT NULL,
            config_json TEXT,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Edges (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id) ON DELETE CASCADE,
            FOREIGN KEY (source_node_id) REFERENCES Nodes (node_id) ON DELETE CASCADE,
            FOREIGN KEY (target_node_id) REFERENCES Nodes (node_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Executions (
            execution_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            user_id TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Jobs (
            job_id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL,
            node_id TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            input_data TEXT,
            output_data TEXT,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            finished_at DATETIME,
            workflow_id TEXT,
            FOREIGN KEY (execution_id) REFERENCES Executions (execution_id) ON DELETE CASCADE,
            FOREIGN KEY (node_id) REFERENCES Nodes (node_id) ON DELETE CASCADE,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id) ON DELETE CASCADE
        )
        """)

    def _run_migration_v4(self, cursor):
        """(V4) Add user_id to Jobs table."""
        try:
            cursor.execute("ALTER TABLE Jobs ADD COLUMN user_id TEXT")
            self.logger.info("Added 'user_id' column to 'Jobs' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                self.logger.warning("'user_id' column already exists in 'Jobs'. Skipping.")
            else:
                raise

    def _run_migration_v5(self, cursor):
        """(R5) Add strategy and gas_budget_hint to Executions table."""
        try:
            cursor.execute("ALTER TABLE Executions ADD COLUMN strategy TEXT DEFAULT 'default'")
            self.logger.info("Added 'strategy' column to 'Executions' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                self.logger.warning("'strategy' column already exists in 'Executions'. Skipping.")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE Executions ADD COLUMN gas_budget_hint INTEGER DEFAULT 0")
            self.logger.info("Added 'gas_budget_hint' column to 'Executions' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                self.logger.warning("'gas_budget_hint' column already exists in 'Executions'. Skipping.")
            else:
                raise

    def _run_migration_v6(self, cursor):
        """(V6) Add source_handle and target_handle to Edges for strict routing."""
        try:
            cursor.execute("ALTER TABLE Edges ADD COLUMN source_handle TEXT")
            self.logger.info("Added 'source_handle' column to 'Edges' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise

        try:
            cursor.execute("ALTER TABLE Edges ADD COLUMN target_handle TEXT")
            self.logger.info("Added 'target_handle' column to 'Edges' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise

    def _run_migration_v7(self, cursor):
        """(V7) [PHASE 4] The Iron Bank Storage (App Isolation)."""
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_storage (
            key TEXT NOT NULL,
            owner_app_id TEXT NOT NULL,
            value TEXT, -- JSON Data
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (key, owner_app_id)
        )
        """)
        self.logger.info("Created 'app_storage' table for Iron Bank Protocol.")

    def start(self):
        self.logger.info("DatabaseService started.")

    def stop(self):
        self.logger.info("DatabaseService stopped.")
