import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./call_audits.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CallAuditRecord(Base):
    __tablename__ = "call_audits"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(50), unique=True, index=True)
    customer_sentiment = Column(String(20))
    primary_issue = Column(Text)
    agent_professionalism_score = Column(Integer)
    mandatory_greeting_done = Column(Boolean)
    solution_provided = Column(Text)
    compliance_score_percentage = Column(Float)
    requires_human_review = Column(Boolean, default=False)
    audit_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()