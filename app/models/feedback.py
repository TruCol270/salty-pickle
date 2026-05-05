from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    email = Column(String, nullable=True)
    page = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
