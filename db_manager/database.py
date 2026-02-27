import asyncio
import json
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


@dataclass
class DatabaseInfo:
    id: str
    name: str
    path: str
    description: str = ""
    created_at: float = 0.0
    tables: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._databases: dict[str, DatabaseInfo] = {}
        self._connections: dict[str, sqlite3.Connection] = {}
        self._config_path = Path.home() / ".blacksheep_db_manager" / "config.json"
        self._load_config()

    def _load_config(self):
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    for db_info in config.get("databases", []):
                        info = DatabaseInfo(**db_info)
                        if Path(info.path).exists():
                            self._databases[info.id] = info
            except Exception:
                pass
        else:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

    def _save_config(self):
        config = {
            "databases": [db.to_dict() for db in self._databases.values()]
        }
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def add_database(self, path: str, name: Optional[str] = None, description: str = "") -> DatabaseInfo:
        db_path = Path(path).resolve()
        if not db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {path}")

        for existing_db in self._databases.values():
            if Path(existing_db.path).resolve() == db_path:
                raise ValueError(f"数据库已存在: {existing_db.name}")

        db_id = str(uuid4())
        db_name = name or db_path.stem

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        import time
        db_info = DatabaseInfo(
            id=db_id,
            name=db_name,
            path=str(db_path),
            description=description,
            created_at=time.time(),
            tables=tables
        )
        self._databases[db_id] = db_info
        self._save_config()
        return db_info

    def create_database(self, path: str, name: Optional[str] = None, description: str = "") -> DatabaseInfo:
        db_path = Path(path).resolve()
        if db_path.exists():
            raise FileExistsError(f"数据库文件已存在: {path}")

        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.close()

        db_id = str(uuid4())
        db_name = name or db_path.stem

        import time
        db_info = DatabaseInfo(
            id=db_id,
            name=db_name,
            path=str(db_path),
            description=description,
            created_at=time.time(),
            tables=[]
        )
        self._databases[db_id] = db_info
        self._save_config()
        return db_info

    def remove_database(self, db_id: str) -> bool:
        if db_id in self._connections:
            try:
                self._connections[db_id].close()
            except Exception:
                pass
            del self._connections[db_id]

        if db_id in self._databases:
            del self._databases[db_id]
            self._save_config()
            return True
        return False

    def get_database(self, db_id: str) -> Optional[DatabaseInfo]:
        return self._databases.get(db_id)

    def list_databases(self) -> list[DatabaseInfo]:
        return list(self._databases.values())

    def _get_connection(self, db_id: str) -> sqlite3.Connection:
        db_info = self._databases.get(db_id)
        if not db_info:
            raise ValueError(f"数据库不存在: {db_id}")

        if db_id not in self._connections:
            self._connections[db_id] = sqlite3.connect(db_info.path)
            self._connections[db_id].row_factory = sqlite3.Row

        return self._connections[db_id]

    def execute_query(self, db_id: str, sql: str, params: Optional[tuple] = None) -> dict[str, Any]:
        conn = self._get_connection(db_id)
        cursor = conn.cursor()

        try:
            cursor.execute(sql, params or ())

            if sql.strip().upper().startswith(("SELECT", "PRAGMA", "EXPLAIN")):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return {
                    "success": True,
                    "columns": columns,
                    "rows": [dict(row) for row in rows],
                    "row_count": len(rows)
                }
            else:
                conn.commit()
                self._refresh_tables(db_id)
                return {
                    "success": True,
                    "row_count": cursor.rowcount,
                    "last_insert_id": cursor.lastrowid if cursor.lastrowid else None
                }
        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def execute_many(self, db_id: str, sql: str, params_list: list[tuple]) -> dict[str, Any]:
        conn = self._get_connection(db_id)
        cursor = conn.cursor()

        try:
            cursor.executemany(sql, params_list)
            conn.commit()
            return {"success": True, "row_count": cursor.rowcount}
        except sqlite3.Error as e:
            conn.rollback()
            return {"success": False, "error": str(e)}

    def get_table_data(self, db_id: str, table_name: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return self.execute_query(
            db_id,
            f"SELECT * FROM `{table_name}` LIMIT ? OFFSET ?",
            (limit, offset)
        )

    def get_table_schema(self, db_id: str, table_name: str) -> dict[str, Any]:
        columns_result = self.execute_query(db_id, f"PRAGMA table_info(`{table_name}`)")
        indexes_result = self.execute_query(db_id, f"PRAGMA index_list(`{table_name}`)")

        indexes = []
        if indexes_result.get("success") and indexes_result.get("rows"):
            for idx in indexes_result["rows"]:
                idx_info = self.execute_query(db_id, f"PRAGMA index_info(`{idx['name']}`)")
                indexes.append({
                    "name": idx["name"],
                    "unique": idx["unique"],
                    "columns": [c["name"] for c in idx_info.get("rows", [])] if idx_info.get("success") else []
                })

        return {
            "success": columns_result.get("success", False),
            "columns": columns_result.get("rows", []),
            "indexes": indexes
        }

    def _refresh_tables(self, db_id: str):
        db_info = self._databases.get(db_id)
        if not db_info:
            return

        conn = sqlite3.connect(db_info.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        db_info.tables = [row[0] for row in cursor.fetchall()]
        conn.close()

    def close_connection(self, db_id: str):
        if db_id in self._connections:
            try:
                self._connections[db_id].close()
            except Exception:
                pass
            del self._connections[db_id]

    def close_all(self):
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()
