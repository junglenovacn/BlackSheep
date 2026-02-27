from dataclasses import dataclass
from pathlib import Path
import os
import struct

from blacksheep import Application, FromJSON, json, get, post, delete

from .database import DatabaseManager


db_manager = DatabaseManager()


@dataclass
class AddDatabaseRequest:
    path: str
    name: str = ""
    description: str = ""


@dataclass
class CreateDatabaseRequest:
    path: str
    name: str = ""
    description: str = ""


@dataclass
class ExecuteQueryRequest:
    sql: str
    params: list = None


app = Application()


def is_sqlite_file(file_path):
    try:
        if os.path.getsize(file_path) < 100:
            return False
        with open(file_path, 'rb') as f:
            header = f.read(16)
            return header[:16] == b'SQLite format 3\x00'
    except:
        return False


@dataclass
class ScanDirRequest:
    path: str
    recursive: bool = False


@post("/api/scan-directory")
async def scan_directory(data: FromJSON[ScanDirRequest]):
    dir_path = data.value.path
    recursive = data.value.recursive or False
    
    try:
        if not os.path.exists(dir_path):
            return json({"success": False, "error": "目录不存在"}, status=404)
        if not os.path.isdir(dir_path):
            return json({"success": False, "error": "路径不是目录"}, status=400)
        
        sqlite_files = []
        extensions = ('.db', '.sqlite', '.sqlite3', '.db3')
        
        if recursive:
            for root, dirs, files in os.walk(dir_path):
                for f in files:
                    if f.lower().endswith(extensions):
                        full_path = os.path.join(root, f)
                        if is_sqlite_file(full_path):
                            sqlite_files.append({
                                "path": full_path,
                                "name": f,
                                "size": os.path.getsize(full_path)
                            })
        else:
            for f in os.listdir(dir_path):
                full_path = os.path.join(dir_path, f)
                if os.path.isfile(full_path) and f.lower().endswith(extensions):
                    if is_sqlite_file(full_path):
                        sqlite_files.append({
                            "path": full_path,
                            "name": f,
                            "size": os.path.getsize(full_path)
                        })
        
        return json({"success": True, "files": sqlite_files})
    except Exception as e:
        return json({"success": False, "error": str(e)}, status=500)


@get("/api/databases")
async def list_databases():
    databases = db_manager.list_databases()
    return json({"success": True, "databases": [db.to_dict() for db in databases]})


@get("/api/databases/{db_id}")
async def get_database(db_id: str):
    db_info = db_manager.get_database(db_id)
    if db_info:
        return json({"success": True, "database": db_info.to_dict()})
    return json({"success": False, "error": "数据库不存在"}, status=404)


@post("/api/databases")
async def add_database(data: FromJSON[AddDatabaseRequest]):
    try:
        result = db_manager.add_database(data.value.path, data.value.name or None, data.value.description)
        return json({"success": True, "database": result.to_dict()})
    except FileNotFoundError as e:
        return json({"success": False, "error": str(e)}, status=404)
    except ValueError as e:
        return json({"success": False, "error": str(e)}, status=400)


@post("/api/databases/create")
async def create_database(data: FromJSON[CreateDatabaseRequest]):
    try:
        result = db_manager.create_database(data.value.path, data.value.name or None, data.value.description)
        return json({"success": True, "database": result.to_dict()})
    except FileExistsError as e:
        return json({"success": False, "error": str(e)}, status=409)
    except Exception as e:
        return json({"success": False, "error": str(e)}, status=400)


@delete("/api/databases/{db_id}")
async def remove_database(db_id: str):
    result = db_manager.remove_database(db_id)
    if result:
        return json({"success": True})
    return json({"success": False, "error": "数据库不存在"}, status=404)


@get("/api/databases/{db_id}/tables")
async def list_tables(db_id: str):
    db_info = db_manager.get_database(db_id)
    if db_info:
        return json({"success": True, "tables": db_info.tables})
    return json({"success": False, "error": "数据库不存在"}, status=404)


@get("/api/databases/{db_id}/tables/{table_name}/data")
async def get_table_data(db_id: str, table_name: str, limit: int = 100, offset: int = 0):
    result = db_manager.get_table_data(db_id, table_name, limit, offset)
    return json(result)


@get("/api/databases/{db_id}/tables/{table_name}/schema")
async def get_table_schema(db_id: str, table_name: str):
    result = db_manager.get_table_schema(db_id, table_name)
    return json(result)


@post("/api/databases/{db_id}/query")
async def execute_query(db_id: str, data: FromJSON[ExecuteQueryRequest]):
    params = tuple(data.value.params) if data.value.params else None
    result = db_manager.execute_query(db_id, data.value.sql, params)
    return json(result)


current_dir = Path(__file__).parent
static_files_dir = current_dir / "static"

if static_files_dir.exists():
    app.serve_files(static_files_dir, root_path="", fallback_document="index.html")
