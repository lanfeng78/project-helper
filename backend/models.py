# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, event
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
from config import settings

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    repo_url = Column(String(512), nullable=False)
    repo_name = Column(String(256), nullable=False)
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    progress_msg = Column(String(512), default="")
    tech_stack = Column(Text, default="")
    report_json = Column(Text, default="")
    report_markdown = Column(Text, default="")
    error_msg = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False, "timeout": 30}
)

# Enable WAL mode for concurrent reads during writes
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
