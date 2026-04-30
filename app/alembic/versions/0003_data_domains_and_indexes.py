"""Add integration + analytics domains and hot-path indexes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strava_sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("after_cursor", sa.DateTime(), nullable=True),
        sa.Column("activities_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("workouts_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_strava_sync_runs_user_started",
        "strava_sync_runs",
        ["user_id", "started_at"],
    )

    op.create_table(
        "google_calendar_sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("events_attempted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_google_calendar_sync_runs_user_started",
        "google_calendar_sync_runs",
        ["user_id", "started_at"],
    )
    op.create_index(
        "ix_google_calendar_sync_runs_plan_started",
        "google_calendar_sync_runs",
        ["plan_id", "started_at"],
    )

    op.create_table(
        "whoop_recovery_samples",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("whoop_user_id", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="api"),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("cycle_id", sa.String(), nullable=True),
        sa.Column("recovery_score", sa.Integer(), nullable=True),
        sa.Column("resting_heart_rate", sa.Integer(), nullable=True),
        sa.Column("hrv_rmssd_milli", sa.Integer(), nullable=True),
        sa.Column("spo2_percentage", sa.Float(), nullable=True),
        sa.Column("skin_temp_celsius", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_whoop_recovery_samples_user_recorded",
        "whoop_recovery_samples",
        ["user_id", "recorded_at"],
    )
    op.create_index(
        "ix_whoop_recovery_samples_cycle",
        "whoop_recovery_samples",
        ["cycle_id"],
    )

    op.create_table(
        "provider_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("provider_user_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="started"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_provider_webhook_events_provider_received",
        "provider_webhook_events",
        ["provider", "received_at"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_provider_webhook_events_success_event "
        "ON provider_webhook_events(provider, event_id) "
        "WHERE event_id IS NOT NULL AND status = 'success'"
    )
    op.create_index(
        "ix_provider_webhook_events_user_received",
        "provider_webhook_events",
        ["user_id", "received_at"],
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id"), nullable=True),
        sa.Column("event_name", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_analytics_events_name_occurred",
        "analytics_events",
        ["event_name", "occurred_at"],
    )
    op.create_index(
        "ix_analytics_events_user_occurred",
        "analytics_events",
        ["user_id", "occurred_at"],
    )

    op.create_table(
        "plan_performance_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id"), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(), nullable=False),
        sa.Column("matched_workouts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_score", sa.Float(), nullable=True),
        sa.Column("adjustments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recovery_recommendation", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_plan_performance_snapshots_plan_time",
        "plan_performance_snapshots",
        ["plan_id", "snapshot_at"],
    )

    # Hot-path indexes for existing query patterns.
    op.create_index(
        "ix_training_plans_user_status",
        "training_plans",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_planned_workouts_plan_completed_scheduled",
        "planned_workouts",
        ["plan_id", "completed", "scheduled_date"],
    )
    op.create_index(
        "ix_completed_workouts_user_start_time",
        "completed_workouts",
        ["user_id", "start_time"],
    )
    op.create_index(
        "ix_completed_workouts_user_source_source_id",
        "completed_workouts",
        ["user_id", "source", "source_id"],
        unique=True,
    )
    op.create_index(
        "ix_adjustment_logs_plan_created",
        "adjustment_logs",
        ["plan_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_adjustment_logs_plan_created", table_name="adjustment_logs")
    op.drop_index(
        "ix_completed_workouts_user_source_source_id",
        table_name="completed_workouts",
    )
    op.drop_index("ix_completed_workouts_user_start_time", table_name="completed_workouts")
    op.drop_index(
        "ix_planned_workouts_plan_completed_scheduled",
        table_name="planned_workouts",
    )
    op.drop_index("ix_training_plans_user_status", table_name="training_plans")

    op.drop_index(
        "ix_plan_performance_snapshots_plan_time",
        table_name="plan_performance_snapshots",
    )
    op.drop_table("plan_performance_snapshots")

    op.drop_index("ix_analytics_events_user_occurred", table_name="analytics_events")
    op.drop_index("ix_analytics_events_name_occurred", table_name="analytics_events")
    op.drop_table("analytics_events")

    op.drop_index(
        "ix_provider_webhook_events_user_received",
        table_name="provider_webhook_events",
    )
    op.drop_index(
        "uq_provider_webhook_events_success_event",
        table_name="provider_webhook_events",
    )
    op.drop_index(
        "ix_provider_webhook_events_provider_received",
        table_name="provider_webhook_events",
    )
    op.drop_table("provider_webhook_events")

    op.drop_index("ix_whoop_recovery_samples_cycle", table_name="whoop_recovery_samples")
    op.drop_index(
        "ix_whoop_recovery_samples_user_recorded",
        table_name="whoop_recovery_samples",
    )
    op.drop_table("whoop_recovery_samples")

    op.drop_index(
        "ix_google_calendar_sync_runs_plan_started",
        table_name="google_calendar_sync_runs",
    )
    op.drop_index(
        "ix_google_calendar_sync_runs_user_started",
        table_name="google_calendar_sync_runs",
    )
    op.drop_table("google_calendar_sync_runs")

    op.drop_index("ix_strava_sync_runs_user_started", table_name="strava_sync_runs")
    op.drop_table("strava_sync_runs")
