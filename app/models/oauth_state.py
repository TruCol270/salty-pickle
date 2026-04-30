from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, unique=True, nullable=False, index=True)
    provider = Column(String, nullable=False)
    redirect_url = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
