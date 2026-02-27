/**
 * SQLite Database Manager - Frontend Application
 */

// State
let currentDbId = null;
let currentTableName = null;
let currentPage = 0;
const pageSize = 100;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDatabases();
});

// API Functions
async function apiGet(url) {
    const response = await fetch(url);
    return await response.json();
}

async function apiPost(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return await response.json();
}

async function apiDelete(url) {
    const response = await fetch(url, { method: 'DELETE' });
    return await response.json();
}

// Database Management
async function loadDatabases() {
    try {
        const result = await apiGet('/api/databases');
        if (result.success) {
            renderDatabaseList(result.databases);
        }
    } catch (error) {
        console.error('Failed to load databases:', error);
    }
}

function renderDatabaseList(databases) {
    const container = document.getElementById('databaseList');
    
    if (databases.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>暂无数据库</p>
                <p style="font-size: 0.75rem; margin-top: 5px;">点击 + 添加数据库</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = databases.map(db => `
        <div class="database-item ${db.id === currentDbId ? 'active' : ''}" 
             onclick="selectDatabase('${db.id}')">
            <i class="fas fa-database"></i>
            <div class="database-info">
                <div class="database-name">${escapeHtml(db.name)}</div>
                <div class="database-path" title="${escapeHtml(db.path)}">${escapeHtml(db.path)}</div>
            </div>
        </div>
    `).join('');
}

async function selectDatabase(dbId) {
    currentDbId = dbId;
    currentTableName = null;
    currentPage = 0;
    
    // Update UI
    document.querySelectorAll('.database-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Load database info
    const result = await apiGet('/api/databases');
    if (result.success) {
        const db = result.databases.find(d => d.id === dbId);
        if (db) {
            document.getElementById('currentDbName').textContent = db.name;
            document.getElementById('currentTableName').textContent = '';
        }
    }
    
    // Show database view
    showView('databaseView');
    
    // Load tables
    loadTables(dbId);
}

async function loadTables(dbId) {
    const grid = document.getElementById('tablesGrid');
    grid.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i></div>';
    
    try {
        const result = await apiGet(`/api/databases/${dbId}/tables`);
        if (result.success) {
            renderTables(result.tables);
        } else {
            grid.innerHTML = `<div class="message message-error">${result.error}</div>`;
        }
    } catch (error) {
        grid.innerHTML = `<div class="message message-error">加载失败: ${error.message}</div>`;
    }
}

function renderTables(tables) {
    const grid = document.getElementById('tablesGrid');
    
    if (tables.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-table"></i>
                <p>该数据库没有数据表</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = tables.map(table => `
        <div class="table-card">
            <div class="table-card-header">
                <i class="fas fa-table"></i>
                <span class="table-card-title">${escapeHtml(table.name)}</span>
            </div>
            <div class="table-card-actions">
                <button class="btn" onclick="viewTableData('${table.name}')">
                    <i class="fas fa-eye"></i> 查看数据
                </button>
                <button class="btn" onclick="viewTableSchema('${table.name}')">
                    <i class="fas fa-info-circle"></i> 结构
                </button>
            </div>
        </div>
    `).join('');
}

// Table Data View
async function viewTableData(tableName) {
    currentTableName = tableName;
    currentPage = 0;
    
    document.getElementById('currentTableName').textContent = `> ${tableName}`;
    showView('tableView');
    
    await loadTableData(tableName, currentPage);
}

async function loadTableData(tableName, page) {
    const container = document.getElementById('dataTable');
    container.innerHTML = '<tr><td colspan="100" class="loading"><i class="fas fa-spinner"></i></td></tr>';
    
    try {
        const offset = page * pageSize;
        const result = await apiGet(
            `/api/databases/${currentDbId}/tables/${tableName}/data?limit=${pageSize}&offset=${offset}`
        );
        
        if (result.success) {
            renderTableData(result);
            renderPagination(result.total_rows, page);
        } else {
            container.innerHTML = `<tr><td colspan="100" class="message message-error">${result.error}</td></tr>`;
        }
    } catch (error) {
        container.innerHTML = `<tr><td colspan="100" class="message message-error">加载失败: ${error.message}</td></tr>`;
    }
}

function renderTableData(result) {
    const table = document.getElementById('dataTable');
    
    if (result.columns.length === 0) {
        table.innerHTML = '<tr><td>无数据</td></tr>';
        return;
    }
    
    // Header
    const headerHtml = `
        <thead>
            <tr>
                ${result.columns.map(col => `<th>${escapeHtml(col)}</th>`).join('')}
            </tr>
        </thead>
    `;
    
    // Body
    const bodyHtml = `
        <tbody>
            ${result.data.map(row => `
                <tr>
                    ${result.columns.map(col => {
                        const value = row[col];
                        let displayValue = value === null ? '<em>NULL</em>' : escapeHtml(String(value));
                        return `<td title="${escapeHtml(String(value))}">${displayValue}</td>`;
                    }).join('')}
                </tr>
            `).join('')}
        </tbody>
    `;
    
    table.innerHTML = headerHtml + bodyHtml;
}

function renderPagination(totalRows, currentPage) {
    const totalPages = Math.ceil(totalRows / pageSize);
    const container = document.getElementById('pagination');
    
    container.innerHTML = `
        <button onclick="changePage(${currentPage - 1})" ${currentPage === 0 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i>
        </button>
        <span>第 ${currentPage + 1} / ${totalPages} 页 (共 ${totalRows} 行)</span>
        <button onclick="changePage(${currentPage + 1})" ${currentPage >= totalPages - 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

function changePage(page) {
    if (page < 0) return;
    currentPage = page;
    loadTableData(currentTableName, currentPage);
}

// Table Schema
async function viewTableSchema(tableName) {
    try {
        const result = await apiGet(`/api/databases/${currentDbId}/tables/${tableName}`);
        if (result.success) {
            renderSchemaTable(result.schema.columns);
            document.getElementById('tableSchemaModal').classList.add('active');
        }
    } catch (error) {
        alert('加载表结构失败: ' + error.message);
    }
}

function renderSchemaTable(columns) {
    const table = document.getElementById('schemaTable');
    
    table.innerHTML = `
        <thead>
            <tr>
                <th>列名</th>
                <th>数据类型</th>
                <th>允许空</th>
                <th>默认值</th>
                <th>主键</th>
            </tr>
        </thead>
        <tbody>
            ${columns.map(col => `
                <tr>
                    <td>${escapeHtml(col.name)}</td>
                    <td>${escapeHtml(col.type)}</td>
                    <td>${col.notnull ? '否' : '是'}</td>
                    <td>${col.dflt_value === null ? '<em>NULL</em>' : escapeHtml(String(col.dflt_value))}</td>
                    <td>${col.pk ? '<i class="fas fa-key" style="color: var(--primary-color);"></i>' : ''}</td>
                </tr>
            `).join('')}
        </tbody>
    `;
}

function hideTableSchemaModal() {
    document.getElementById('tableSchemaModal').classList.remove('active');
}

// Query Panel
function showQueryPanel() {
    if (!currentDbId) {
        alert('请先选择一个数据库');
        return;
    }
    showView('queryView');
}

async function executeQuery() {
    const query = document.getElementById('sqlInput').value.trim();
    if (!query) {
        alert('请输入 SQL 查询语句');
        return;
    }
    
    const resultsContainer = document.getElementById('queryResults');
    resultsContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i></div>';
    
    try {
        const result = await apiPost(`/api/databases/${currentDbId}/query`, { query });
        renderQueryResults(result);
    } catch (error) {
        resultsContainer.innerHTML = `<div class="message message-error">执行失败: ${error.message}</div>`;
    }
}

function renderQueryResults(result) {
    const container = document.getElementById('queryResults');
    
    if (!result.success) {
        container.innerHTML = `<div class="message message-error">${escapeHtml(result.error)}</div>`;
        return;
    }
    
    // For non-SELECT queries
    if (result.message) {
        container.innerHTML = `<div class="message message-success">${escapeHtml(result.message)}</div>`;
        return;
    }
    
    // For SELECT queries
    let html = `
        <div class="query-results-header">
            <h4>查询结果</h4>
            <span class="query-results-info">共 ${result.row_count} 行</span>
        </div>
    `;
    
    if (result.columns.length > 0) {
        html += `
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${result.columns.map(col => `<th>${escapeHtml(col)}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${result.data.map(row => `
                            <tr>
                                ${result.columns.map(col => {
                                    const value = row[col];
                                    return `<td>${value === null ? '<em>NULL</em>' : escapeHtml(String(value))}</td>`;
                                }).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function clearQuery() {
    document.getElementById('sqlInput').value = '';
    document.getElementById('queryResults').innerHTML = '';
}

// Add Database Modal
function showAddDatabaseModal() {
    document.getElementById('addDatabaseModal').classList.add('active');
}

function hideAddDatabaseModal() {
    document.getElementById('addDatabaseModal').classList.remove('active');
    // Clear form
    document.getElementById('dbName').value = '';
    document.getElementById('dbPath').value = '';
    document.getElementById('dbDescription').value = '';
}

async function addDatabase() {
    const name = document.getElementById('dbName').value.trim();
    const path = document.getElementById('dbPath').value.trim();
    const description = document.getElementById('dbDescription').value.trim();
    
    if (!name || !path) {
        alert('请填写数据库名称和路径');
        return;
    }
    
    try {
        const result = await apiPost('/api/databases', { name, path, description });
        if (result.success) {
            hideAddDatabaseModal();
            loadDatabases();
        } else {
            alert('添加失败: ' + result.error);
        }
    } catch (error) {
        alert('添加失败: ' + error.message);
    }
}

function browseFile() {
    // Create a hidden file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.db,.sqlite,.sqlite3,.db3';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // For security reasons, we can only get the filename, not the full path
            // In a real app, you might need a different approach
            document.getElementById('dbPath').value = file.name;
            // Auto-fill name if empty
            if (!document.getElementById('dbName').value) {
                document.getElementById('dbName').value = file.name.replace(/\.[^/.]+$/, '');
            }
        }
    };
    input.click();
}

// Remove Database
async function removeCurrentDatabase() {
    if (!currentDbId) {
        alert('请先选择一个数据库');
        return;
    }
    
    if (!confirm('确定要移除此数据库吗？这不会删除实际的数据库文件。')) {
        return;
    }
    
    try {
        const result = await apiDelete(`/api/databases/${currentDbId}`);
        if (result.success) {
            currentDbId = null;
            currentTableName = null;
            document.getElementById('currentDbName').textContent = '';
            document.getElementById('currentTableName').textContent = '';
            showView('welcomeScreen');
            loadDatabases();
        } else {
            alert('移除失败: ' + result.error);
        }
    } catch (error) {
        alert('移除失败: ' + error.message);
    }
}

// View Management
function showView(viewId) {
    // Hide all views
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('databaseView').style.display = 'none';
    document.getElementById('tableView').style.display = 'none';
    document.getElementById('queryView').style.display = 'none';
    
    // Show selected view
    document.getElementById(viewId).style.display = 'block';
}

// Utility Functions
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// Close modals on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}
