import uvicorn
from .api import app

def run(host: str = "127.0.0.1", port: int = 8200):
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     SQLite 数据库管理工具                                  ║
║                                                           ║
║     启动中...                                              ║
║                                                           ║
║     访问地址: http://{host}:{port}                         ║
║     API文档: http://{host}:{port}/docs                    ║
║                                                           ║
║     按 Ctrl+C 停止服务                                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run()
