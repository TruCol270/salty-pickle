"""Baseline schema — captures all existing tables.

Revision ID: 0001
Revises: (none)
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("strava_athlete_id", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("google_calendar_id", sa.String(), nullable=True),
        sa.Column("strava_access_token", sa.String(), nullable=True),
        sa.Column("strava_refresh_token", sa.String(), nullable=True),
        sa.Column("strava_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("google_access_token", sa.String(), nullable=True),
        sa.Column("google_refresh_token", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), server_default="America/New_York"),
        sa.Column("units", sa.String(), server_default="km"),
        sa.Column("preferred_workout_days", sa.String(), nullable=True),
        sa.Column("preferred_workout_time", sa.String(), server_default="morning"),
        sa.Column("available_equipment", sa.String(), nullable=True),
        sa.Column("injury_history", sa.String(), nullable=True),
        sa.Column("sleep_hours_target", sa.Float(), nullable=True),
        sa.Column("min_recovery_threshold", sa.Float(), server_default="30.0"),
        sa.Column("low_hrv_threshold_ms", sa.Float(), server_default="20.0"),
        sa.Column("whoop_user_id", sa.String(), nullable=True),
        sa.Column("whoop_access_token", sa.String(), nullable=True),
        sa.Column("whoop_refresh_token", sa.String(), nullable=True),
        sa.Column("whoop_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("tenant_id", sa.String(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "training_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("goal_race_name", sa.String(), nullable=True),
        sa.Column("goal_race_date", sa.DateTime(), nullable=True),
        sa.Column("goal_distance_km", sa.Float(), nullable=True),
        sa.Column("goal_time_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("current_week_number", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "planned_workouts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id"), nullable=False, index=True),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("workout_type", sa.String(), nullable=False),
        sa.Column("target_distance_km", sa.Float(), nullable=True),
        sa.Column("target_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("target_pace_min_per_km", sa.Float(), nullable=True),
        sa.Column("target_elevation_m", sa.Float(), nullable=True),
        sa.Column("flexible", sa.String(), server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(), nullable=True),
        sa.Column("calendar_event_id", sa.String(), nullable=True),
        sa.Column("completed", sa.String(), server_default="false"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "completed_workouts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("planned_workout_id", sa.Integer(), sa.ForeignKey("planned_workouts.id"), nullable=True),
        sa.Column("source", sa.String(), server_default="strava"),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("actual_distance_km", sa.Float(), nullable=True),
        sa.Column("actual_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("actual_pace_min_per_km", sa.Float(), nullable=True),
        sa.Column("actual_elevation_m", sa.Float(), nullable=True),
        sa.Column("average_heart_rate", sa.Float(), nullable=True),
        sa.Column("max_heart_rate", sa.Float(), nullable=True),
        sa.Column("average_cadence", sa.Float(), nullable=True),
        sa.Column("performance_score", sa.Float(), nullable=True),
        sa.Column("perceived_effort", sa.Integer(), nullable=True),
        sa.Column("workout_type", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "adjustment_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("completed_workouts.id"), nullable=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id"), nullable=True),
        sa.Column("adjustment_type", sa.String(), nullable=False),
        sa.Column("agent", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changes_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("state", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("redirect_url", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oauth_states")
    op.drop_table("adjustment_logs")
    op.drop_table("completed_workouts")
    op.drop_table("planned_workouts")
    op.drop_table("training_plans")
    op.drop_table("users")
