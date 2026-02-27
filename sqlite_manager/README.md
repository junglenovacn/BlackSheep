# SQLite 数据库管理工具

基于 BlackSheep 框架开发的本地多 SQLite 数据库管理工具。

## 功能特性

- 📁 **多数据库管理** - 轻松添加、查看和管理不同路径下的 SQLite 数据库
- 📊 **表浏览** - 可视化展示数据库中的所有表
- 🔍 **数据查看** - 分页浏览表数据，支持大数据集
- 📋 **表结构** - 查看表的列信息、数据类型、主键等结构信息
- 📝 **SQL 查询** - 执行自定义 SQL 查询语句
- 🎨 **现代化界面** - 简洁美观的 Web 界面

## 项目结构

```
sqlite_manager/
├── __init__.py          # 包初始化
├── app.py               # BlackSheep 应用主入口
├── database.py          # 数据库连接管理模块
├── main.py              # 启动脚本
├── create_test_db.py    # 创建测试数据库
├── static/              # 静态文件
│   ├── index.html       # 主页面
│   ├── style.css        # 样式文件
│   └── app.js           # 前端逻辑
└── README.md            # 说明文档
```

## 安装依赖

确保已安装 BlackSheep 框架：

```bash
pip install -e ..
# 或
pip install blacksheep uvicorn
```

## 使用方法

### 1. 启动应用

```bash
cd sqlite_manager
python main.py
```

或直接使用 uvicorn：

```bash
uvicorn sqlite_manager.app:app --reload --port 8080
```

### 2. 访问应用

打开浏览器访问：http://127.0.0.1:8080

### 3. 添加数据库

1. 点击左侧的 **+** 按钮
2. 输入数据库名称和文件路径
3. 点击"添加"

### 4. 管理数据库

- **查看表列表** - 点击数据库名称
- **查看表数据** - 点击表卡片上的"查看数据"
- **查看表结构** - 点击表卡片上的"结构"
- **执行 SQL** - 点击工具栏的"SQL查询"

## 创建测试数据库

运行以下命令创建示例数据库：

```bash
python create_test_db.py
```

这将在当前目录创建一个 `test_database.db` 文件，包含 users、products 和 orders 三个表。

## API 接口

### 数据库管理

- `GET /api/databases` - 列出所有数据库
- `POST /api/databases` - 添加数据库
- `DELETE /api/databases/{db_id}` - 移除数据库

### 表操作

- `GET /api/databases/{db_id}/tables` - 获取所有表
- `GET /api/databases/{db_id}/tables/{table_name}` - 获取表结构
- `GET /api/databases/{db_id}/tables/{table_name}/data` - 获取表数据（支持 limit/offset 分页）

### 查询

- `POST /api/databases/{db_id}/query` - 执行 SQL 查询

### 统计

- `GET /api/databases/{db_id}/stats` - 获取数据库统计信息

## 配置

数据库配置保存在 `databases.json` 文件中，包含所有已添加的数据库信息。

## 技术栈

- **后端**: Python + BlackSheep + SQLite3
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **图标**: Font Awesome

## 注意事项

1. 数据库文件路径必须是服务器可访问的绝对路径
2. 工具不会修改或删除实际的数据库文件，只会管理连接
3. 建议在生产环境配置适当的访问控制
