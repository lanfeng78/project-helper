# -*- coding: utf-8 -*-
from sqlalchemy import (
    create_engine, inspect, text,
    Column, String, Text, DateTime, Float, Integer, ForeignKey, event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from config import settings

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    repo_url = Column(String(512), nullable=False)
    repo_name = Column(String(256), nullable=False)
    repo_hash = Column(String(64), nullable=False, index=True, default="")
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    progress_msg = Column(String(512), default="")
    tech_stack = Column(Text, default="")
    report_json = Column(Text, default="")
    report_markdown = Column(Text, default="")
    error_msg = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship("User", backref="projects")


engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False, "timeout": 30}
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def init_db():
    inspector = inspect(engine)
    has_users = inspector.has_table("users")
    Base.metadata.create_all(bind=engine)
    # 重新创建 inspector，确保 schema 状态在 create_all 之后是最新的。
    inspector_after = inspect(engine)
    if not has_users and inspector_after.has_table("projects"):
        # 首次引入用户系统——按设计文档决策（spec 3.2），清空历史项目数据。
        # 旧项目无 user_id 归属，无法迁移到新 schema。
        with engine.begin() as conn:
            cols = [c["name"] for c in inspector_after.get_columns("projects")]
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN user_id INTEGER"))
            conn.execute(text("DELETE FROM projects"))
            # sqlite_sequence 只有在表有过 autoincrement 插入后才存在
            if inspector_after.has_table("sqlite_sequence"):
                conn.execute(text("DELETE FROM sqlite_sequence WHERE name='projects'"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
