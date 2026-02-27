"""
Database connection and management module.
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading


@dataclass
class DatabaseInfo:
    """Information about a registered database."""
    id: str
    name: str
    path: str
    description: str = ""
    created_at: str = ""
    last_accessed: str = ""
    size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatabaseManager:
    """Manages multiple SQLite database connections."""
    
    def __init__(self, config_path: str = "databases.json"):
        self.config_path = Path(config_path)
        self.databases: Dict[str, DatabaseInfo] = {}
        self.connections: Dict[str, sqlite3.Connection] = {}
        self.lock = threading.Lock()
        self._load_config()
    
    def _load_config(self):
        """Load database configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for db_id, db_data in data.get('databases', {}).items():
                        self.databases[db_id] = DatabaseInfo(**db_data)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save database configuration to file."""
        try:
            data = {
                'databases': {
                    db_id: db.to_dict() 
                    for db_id, db in self.databases.items()
                }
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def add_database(self, db_info: DatabaseInfo) -> bool:
        """Add a new database to the manager."""
        with self.lock:
            if not os.path.exists(db_info.path):
                return False
            
            db_info.size_bytes = os.path.getsize(db_info.path)
            self.databases[db_info.id] = db_info
            self._save_config()
            return True
    
    def remove_database(self, db_id: str) -> bool:
        """Remove a database from the manager."""
        with self.lock:
            if db_id in self.databases:
                if db_id in self.connections:
                    self.connections[db_id].close()
                    del self.connections[db_id]
                del self.databases[db_id]
                self._save_config()
                return True
            return False
    
    def get_database(self, db_id: str) -> Optional[DatabaseInfo]:
        """Get database information by ID."""
        return self.databases.get(db_id)
    
    def list_databases(self) -> List[DatabaseInfo]:
        """List all registered databases."""
        return list(self.databases.values())
    
    @contextmanager
    def get_connection(self, db_id: str):
        """Get a database connection (context manager)."""
        conn = None
        try:
            db_info = self.databases.get(db_id)
            if not db_info:
                raise ValueError(f"Database {db_id} not found")
            
            conn = sqlite3.connect(db_info.path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, db_id: str, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Execute a SQL query and return results."""
        with self.get_connection(db_id) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT') or \
                   query.strip().upper().startswith('PRAGMA'):
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description] if cursor.description else []
                    data = [dict(row) for row in rows]
                    return {
                        'success': True,
                        'columns': columns,
                        'data': data,
                        'row_count': len(data)
                    }
                else:
                    conn.commit()
                    return {
                        'success': True,
                        'message': f"Query executed successfully. Rows affected: {cursor.rowcount}",
                        'row_count': cursor.rowcount
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
            finally:
                cursor.close()
    
    def get_tables(self, db_id: str) -> List[Dict[str, Any]]:
        """Get all tables in a database."""
        result = self.execute_query(
            db_id, 
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        if result['success']:
            return result['data']
        return []
    
    def get_table_info(self, db_id: str, table_name: str) -> Dict[str, Any]:
        """Get table schema information."""
        result = self.execute_query(db_id, f"PRAGMA table_info({table_name})")
        if result['success']:
            return {
                'columns': result['data'],
                'column_count': len(result['data'])
            }
        return {'columns': [], 'column_count': 0}
    
    def get_table_data(self, db_id: str, table_name: str, 
                       limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get data from a table with pagination."""
        count_result = self.execute_query(
            db_id, 
            f"SELECT COUNT(*) as count FROM {table_name}"
        )
        total_rows = count_result['data'][0]['count'] if count_result['success'] else 0
        
        result = self.execute_query(
            db_id,
            f"SELECT * FROM {table_name} LIMIT ? OFFSET ?",
            (limit, offset)
        )
        
        if result['success']:
            result['total_rows'] = total_rows
            result['limit'] = limit
            result['offset'] = offset
            result['table_name'] = table_name
        
        return result
