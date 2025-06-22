# backend/api_server.py

import os
import random
import string
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# --- 1. 配置 (Configuration) ---

# 从环境变量中读取数据库连接URL，这是容器化部署的最佳实践
# docker-compose.yml 会自动注入这个环境变量
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/shared_storage.db")

# SQLAlchemy 引擎
# connect_args 是专门为SQLite准备的，在多线程环境下是必需的
# PostgreSQL不需要这个参数
engine_args = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_args)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy模型的基础类
Base = declarative_base()


# --- 2. 数据库模型 (SQLAlchemy Models) ---

# 该模型严格对应《架构文档》中定义的 shared_snippets 表
class SharedSnippet(Base):
    __tablename__ = "shared_snippets"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String(12), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(50), default='plaintext')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# --- 3. API数据模型 (Pydantic Models) ---

class SnippetCreate(BaseModel):
    content: str
    language: str = 'plaintext'
    expires_in_days: Optional[int] = Field(None, ge=1)

class SnippetResponse(BaseModel):
    share_id: str
    url: str
    expires_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True # 允许从ORM对象自动映射数据

class SnippetContent(BaseModel):
    content: str
    language: str
    created_at: datetime

    class Config:
        orm_mode = True


# --- 4. FastAPI 应用实例和数据库初始化 ---

app = FastAPI(title="CodeSharer API", version="1.0.0")

# 创建所有定义的表 (如果它们不存在)
# 在一个更复杂的应用中，这通常由Alembic等迁移工具处理
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("数据库表已检查/创建。")

# --- 5. 依赖项 (Dependencies) ---

# FastAPI的依赖注入，为每个请求提供一个独立的数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 6. 辅助函数 (Utility Functions) ---

def generate_share_id(db: Session, length: int = 8) -> str:
    """生成一个在数据库中唯一的随机分享ID"""
    while True:
        share_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        # 检查ID是否已存在于数据库中
        if not db.query(SharedSnippet).filter(SharedSnippet.share_id == share_id).first():
            return share_id


# --- 7. API 端点 (Endpoints) ---

@app.post("/api/snippets", response_model=SnippetResponse, status_code=201, tags=["Snippets"])
def create_snippet(snippet: SnippetCreate, db: Session = Depends(get_db)):
    """
    创建一个新的代码片段分享。
    
    - 接收代码内容、语言和可选的有效期。
    - 生成一个唯一的分享ID。
    - 将片段存入数据库。
    - 返回分享ID、URL和过期时间。
    """
    if not snippet.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    
    share_id = generate_share_id(db)
    
    expires_at = None
    if snippet.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=snippet.expires_in_days)
    
    db_snippet = SharedSnippet(
        share_id=share_id,
        content=snippet.content,
        language=snippet.language,
        expires_at=expires_at
    )
    
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)
    
    # 这里的URL应指向前端展示页面，为方便测试，暂时指向API本身
    # 在生产环境中，可以从环境变量读取基础URL
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    db_snippet.url = f"{base_url}/api/snippets/{share_id}"
    
    print(f"创建了新的分享: ID={share_id}, 有效期至: {expires_at or '永久'}")
    
    return db_snippet


@app.get("/api/snippets/{share_id}", response_model=SnippetContent, tags=["Snippets"])
def get_snippet(share_id: str, db: Session = Depends(get_db)):
    """
    根据分享ID获取一个代码片段的内容。
    
    - 如果片段不存在，返回404。
    - 如果片段已过期，将其从数据库中删除并返回404。
    """
    db_snippet = db.query(SharedSnippet).filter(SharedSnippet.share_id == share_id).first()
    
    if not db_snippet:
        raise HTTPException(status_code=404, detail="Snippet not found.")
    
    if db_snippet.expires_at and db_snippet.expires_at < datetime.utcnow():
        print(f"片段 {share_id} 已过期，正在删除。")
        db.delete(db_snippet)
        db.commit()
        raise HTTPException(status_code=404, detail="Snippet not found or has expired.")
    
    print(f"获取了分享内容: ID={share_id}")
    
    return db_snippet


# --- 8. 直接运行 (For Development) ---
if __name__ == "__main__":
    print("以开发模式启动FastAPI服务器...")
    print(f"数据库类型: {'SQLite' if DATABASE_URL.startswith('sqlite') else 'PostgreSQL'}")
    print(f"数据库位置: {DATABASE_URL}")
    print("访问 http://127.0.0.1:8000/docs 查看API文档")
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)