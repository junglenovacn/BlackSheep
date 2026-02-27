#!/usr/bin/env python3

import uvicorn
from db_manager.api import app

def run(host: str = "127.0.0.1", port: int = 8200):
    """启动数据库管理工具"""
    print(f"BlackSheep SQLite 数据库管理工具")
    print(f"访问地址: http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run()
