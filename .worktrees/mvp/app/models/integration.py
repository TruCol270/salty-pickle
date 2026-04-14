from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON

from app.database import Base


class SyncRunStatus:
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"


class StravaSyncRun(Base):
    __tablename__ = "strava_sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String, default=SyncRunStatus.STARTED, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # Query cursor for replays/debugging.
    after_cursor = Column(DateTime, nullable=True)

    activities_fetched = Column(Integer, default=0, nullable=False)
    workouts_created = Column(Integer, default=0, nullable=False)

    # Keep last error for operator visibility.
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GoogleCalendarSyncRun(Base):
    __tablename__ = "google_calendar_sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=True, index=True)

    status = Column(String, default=SyncRunStatus.STARTED, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    events_attempted = Column(Integer, default=0, nullable=False)
    events_synced = Column(Integer, default=0, nullable=False)

    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WhoopRecoverySample(Base):
    __tablename__ = "whoop_recovery_samples"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    whoop_user_id = Column(String, nullable=True, index=True)

    # Source metadata enables replay and de-duplication logic.
    source = Column(String, default="api", nullable=False)
    source_id = Column(String, nullable=True)

    cycle_id = Column(String, nullable=True, index=True)
    recovery_score = Column(Integer, nullable=True)
    resting_heart_rate = Column(Integer, nullable=True)
    hrv_rmssd_milli = Column(Integer, nullable=True)
    spo2_percentage = Column(Float, nullable=True)
    skin_temp_celsius = Column(Float, nullable=True)

    recorded_at = Column(DateTime, nullable=True)
    payload = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProviderWebhookEvent(Base):
    __tablename__ = "provider_webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=True, index=True)
    provider_user_id = Column(String, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    event_id = Column(String, nullable=True, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String, default=SyncRunStatus.STARTED, nullable=False)

    error_message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
