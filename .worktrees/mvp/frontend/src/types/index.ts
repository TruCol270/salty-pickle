/** Shared API-facing types (import from here instead of duplicating per page). */

export interface Workout {
  id: number;
  name: string;
  workout_type: string;
  distance_km: number;
  duration_minutes: number;
  avg_pace_min_per_km: number | null;
  avg_heartrate: number | null;
  elevation_gain_m: number | null;
  start_time: string;
}

export interface WorkoutStats {
  total_workouts: number;
  total_distance_km: number;
  average_pace: number | null;
  workouts_by_type: Record<string, number>;
  weekly_distances: { week: string; distance_km: number }[];
}

export interface TrainingPlanSummary {
  id: number;
  name: string;
  status: string;
  [key: string]: unknown;
}

export interface PlannedWorkout {
  id: number;
  workout_type: string;
  scheduled_date: string | null;
  target_distance_km: number | null;
  [key: string]: unknown;
}

export interface UserPreferences {
  preferred_workout_days: string;
  preferred_workout_time: string;
  available_equipment: string;
  injury_history: string;
  sleep_hours_target: number | null;
}

export interface IntegrationStatus {
  strava: { connected: boolean; athlete_id?: string | null };
  google: { connected: boolean; calendar_id?: string | null };
  whoop: { connected: boolean; user_id?: string | null };
}

export interface WhoopRecoveryPoint {
  label: string;
  recovery: number;
  hrv: number | null;
  rhr: number | null;
}
