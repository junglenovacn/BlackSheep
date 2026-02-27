"""
Main application module for SQLite Database Manager.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path

import uvicorn
from blacksheep import Application, Request, Response, json, text, file, html
from blacksheep.contents import Content
from blacksheep.server.responses import redirect

from sqlite_manager.database import DatabaseManager, DatabaseInfo

app = Application(show_error_details=True)
db_manager = DatabaseManager()

static_path = Path(__file__).parent / "static"


@app.router.get("/")
async def index():
    """Serve main page."""
    index_file = static_path / "index.html"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return html(content)
    return text("Welcome to SQLite Database Manager")


@app.router.get("/static/style.css")
async def serve_css():
    """Serve CSS file."""
    css_file = static_path / "style.css"
    if css_file.exists():
        with open(css_file, 'rb') as f:
            content = f.read()
        return Response(200, content=Content(b"text/css", content))
    return Response(404, content=text("Not found"))


@app.router.get("/static/app.js")
async def serve_js():
    """Serve JS file."""
    js_file = static_path / "app.js"
    if js_file.exists():
        with open(js_file, 'rb') as f:
            content = f.read()
        return Response(200, content=Content(b"application/javascript", content))
    return Response(404, content=text("Not found"))


@app.router.get("/api/databases")
async def list_databases():
    """List all registered databases."""
    databases = db_manager.list_databases()
    return json({
        'success': True,
        'databases': [db.to_dict() for db in databases]
    })


@app.router.post("/api/databases")
async def add_database(request: Request):
    """Add a new database."""
    data = await request.json()
    
    name = data.get('name', '').strip()
    path = data.get('path', '').strip()
    description = data.get('description', '').strip()
    
    if not name or not path:
        return json({
            'success': False,
            'error': 'Name and path are required'
        }, status=400)
    
    if not os.path.exists(path):
        return json({
            'success': False,
            'error': 'Database file does not exist'
        }, status=400)
    
    db_id = str(uuid.uuid4())[:8]
    db_info = DatabaseInfo(
        id=db_id,
        name=name,
        path=path,
        description=description,
        created_at=datetime.now().isoformat()
    )
    
    if db_manager.add_database(db_info):
        return json({
            'success': True,
            'database': db_info.to_dict()
        })
    else:
        return json({
            'success': False,
            'error': 'Failed to add database'
        }, status=500)


@app.router.delete("/api/databases/:db_id")
async def remove_database(db_id: str):
    """Remove a database from the manager."""
    if db_manager.remove_database(db_id):
        return json({'success': True})
    else:
        return json({
            'success': False,
            'error': 'Database not found'
        }, status=404)


@app.router.get("/api/databases/:db_id/tables")
async def get_tables(db_id: str):
    """Get all tables in a database."""
    db_info = db_manager.get_database(db_id)
    if not db_info:
        return json({
            'success': False,
            'error': 'Database not found'
        }, status=404)
    
    tables = db_manager.get_tables(db_id)
    return json({
        'success': True,
        'tables': tables
    })


@app.router.get("/api/databases/:db_id/tables/:table_name")
async def get_table_info(db_id: str, table_name: str):
    """Get table schema and data."""
    db_info = db_manager.get_database(db_id)
    if not db_info:
        return json({
            'success': False,
            'error': 'Database not found'
        }, status=404)
    
    schema = db_manager.get_table_info(db_id, table_name)
    return json({
        'success': True,
        'schema': schema
    })


@app.router.get("/api/databases/:db_id/tables/:table_name/data")
async def get_table_data(db_id: str, table_name: str, 
                         limit: int = 100, offset: int = 0):
    """Get table data with pagination."""
    db_info = db_manager.get_database(db_id)
    if not db_info:
        return json({
            'success': False,
            'error': 'Database not found'
        }, status=404)
    
    result = db_manager.get_table_data(db_id, table_name, limit, offset)
    return json(result)


@app.router.post("/api/databases/:db_id/query")
async def execute_query(db_id: str, request: Request):
    """Execute a SQL query."""
    db_info = db_manager.get_database(db_id)
    if not db_info:
        return json({
            'success': False,
            'error': 'Database not found'
        }, status=404)
    
    data = await request.json()
    query = data.get('query', '').strip()
    
    if not query:
        return json({
            'success': False,
            'error': 'Query is required'
        }, status=400)
    
    result = db_manager.execute_query(db_id, query)
    return json(result)


@app.router.get("/api/databases/:db_id/stats")
async def get_database_stats(db_id: str):
    """Get database statistics."""
    db_info = db_manager.get_database(db_id)
    if not db_info:
        return json({
            'success': False,
            'error': 'Database not found'
        }, status=404)
    
    tables = db_manager.get_tables(db_id)
    table_count = len(tables)
    
    total_rows = 0
    for table in tables:
        table_name = table.get('name')
        if table_name:
            result = db_manager.execute_query(
                db_id, 
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            if result['success'] and result['data']:
                total_rows += result['data'][0].get('count', 0)
    
    return json({
        'success': True,
        'stats': {
            'table_count': table_count,
            'total_rows': total_rows,
            'file_size': db_info.size_bytes,
            'file_size_formatted': format_file_size(db_info.size_bytes)
        }
    })


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
