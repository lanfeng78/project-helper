# -*- coding: utf-8 -*-
from sqlalchemy import (
    create_engine, inspect, text,
    Column, String, Text, DateTime, Float, Integer, ForeignKey, event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from config import settings

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    repo_url = Column(String(512), nullable=False)
    repo_name = Column(String(256), nullable=False)
    repo_hash = Column(String(64), nullable=False, index=True, default="")
    analysis_mode = Column(String(16), default="detail")  # "simple" | "detail"
    model_used = Column(String(64), default="")
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    progress_msg = Column(String(512), default="")
    tech_stack = Column(Text, default="")
    report_json = Column(Text, default="")
    report_markdown = Column(Text, default="")
    error_msg = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class QASession(Base):
    """一次 QA 对话(豆包侧边栏的"一条对话")。

    title 默认占位"新对话",首条用户消息发出后用其前 40 字符回填。
    """
    __tablename__ = "qa_sessions"

    id = Column(String(36), primary_key=True)  # uuid4 hex
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(120), default="新对话")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages = relationship(
        "QAMessage",
        backref="session",
        cascade="all, delete-orphan",
        order_by="QAMessage.id",
    )


class QAMessage(Base):
    """会话内的单条消息(role + content)。

    顺序由自增 id 决定;同一 session 内 id 递增即为发送顺序。
    """
    __tablename__ = "qa_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(36),
        ForeignKey("qa_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(16), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


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
    """建表 + 老库兼容迁移。

    用户系统已废弃 → 启动时直接丢弃残留的 users 表与 projects.user_id 列。
    详见 README/git history;之前的 user-scoped 数据这里一律清空,因为
    user_id NOT NULL 约束无法在不指派归属的情况下保留旧行。
    """
    inspector_before = inspect(engine)
    legacy_users = inspector_before.has_table("users")
    cols_before = (
        {c["name"] for c in inspector_before.get_columns("projects")}
        if inspector_before.has_table("projects")
        else set()
    )

    if legacy_users or "user_id" in cols_before:
        # SQLite 不支持直接 DROP COLUMN(老版本),最稳妥的做法是清空 projects
        # + 整表重建。本工具的数据本就只是分析缓存,清掉无副作用。
        with engine.begin() as conn:
            if inspector_before.has_table("projects"):
                conn.execute(text("DROP TABLE projects"))
            if inspector_before.has_table("qa_sessions"):
                conn.execute(text("DROP TABLE qa_sessions"))
            if inspector_before.has_table("qa_messages"):
                conn.execute(text("DROP TABLE qa_messages"))
            if legacy_users:
                conn.execute(text("DROP TABLE users"))

    Base.metadata.create_all(bind=engine)

    # ── analysis_mode / model_used 增量迁移 ──
    # 这两列在 v1.2 引入;若执行了上面的 DROP 逻辑,create_all 已经包含它们,
    # 这里仅对未触发 DROP 的更老 schema 兜底。
    inspector_after = inspect(engine)
    if inspector_after.has_table("projects"):
        cols = {c["name"] for c in inspector_after.get_columns("projects")}
        with engine.begin() as conn:
            if "analysis_mode" not in cols:
                conn.execute(text(
                    "ALTER TABLE projects ADD COLUMN analysis_mode VARCHAR(16) DEFAULT 'detail'"
                ))
            if "model_used" not in cols:
                conn.execute(text(
                    "ALTER TABLE projects ADD COLUMN model_used VARCHAR(64) DEFAULT ''"
                ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
