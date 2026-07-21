from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    content = Column(Text, nullable=False)

    category = Column(String)
    priority = Column(String)
    sentiment = Column(String)
    ai_confidence = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
