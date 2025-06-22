# database/db_handler.py

import sqlite3
import os
from datetime import datetime

# 定义数据库文件路径
DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'local_storage.db')

def get_db_connection():
    """获取数据库连接"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # 使用 Row 工厂使得查询结果可以像字典一样通过列名访问
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    初始化数据库，创建 snippets 表。
    该函数符合《架构文档》定义的本地数据库模式。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 架构文档中的 SQL Schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS snippets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        language VARCHAR(50) DEFAULT 'plaintext',
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 创建一个触发器，在更新行时自动更新 updated_at 字段
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_snippets_updated_at
    AFTER UPDATE ON snippets
    FOR EACH ROW
    BEGIN
        UPDATE snippets SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;
    """)

    conn.commit()
    conn.close()
    print("数据库初始化成功。")

# --- CRUD 操作 ---

def add_snippet(title: str, content: str, language: str = 'plaintext') -> int:
    """
    添加一个新的代码片段。
    对应 "FR1: 创建、保存新的代码片段"。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO snippets (title, content, language) VALUES (?, ?, ?)",
        (title, content, language)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_all_snippets() -> list:
    """
    获取所有代码片段的列表，按更新时间降序排列。
    对应 "FR4: 列表展示所有代码片段"。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, language, updated_at FROM snippets ORDER BY updated_at DESC")
    snippets = cursor.fetchall()
    conn.close()
    return [dict(row) for row in snippets]

def get_snippet_by_id(snippet_id: int) -> dict:
    """根据ID获取单个代码片段的完整内容。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,))
    snippet = cursor.fetchone()
    conn.close()
    return dict(snippet) if snippet else None

def update_snippet(snippet_id: int, title: str, content: str, language: str):
    """
    更新一个已有的代码片段。
    对应 "FR2: 查看和编辑已有的代码片段"。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE snippets SET title = ?, content = ?, language = ? WHERE id = ?",
        (title, content, language, snippet_id)
    )
    conn.commit()
    conn.close()

def delete_snippet(snippet_id: int):
    """
    删除一个代码片段。
    对应 "FR3: 删除不需要的代码片段"。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
    conn.commit()
    conn.close()

# 在首次导入此模块时，自动检查并初始化数据库
if __name__ == '__main__':
    print(f"数据库文件位于: {DB_PATH}")
    init_db()
    # 可以添加一些测试数据
    # if not get_all_snippets():
    #     add_snippet("示例: Python", "print('Hello from CodeSharer!')", "python")
    #     add_snippet("示例: SQL", "SELECT * FROM snippets;", "sql")
    #     print("已添加示例数据。")
    # print(get_all_snippets())