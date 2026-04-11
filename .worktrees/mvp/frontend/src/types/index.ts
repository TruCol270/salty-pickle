export interface Workout {
  id: number;
  user_id: number;
  source: string;
  start_time: string;
  actual_distance_km: number | null;
  actual_duration_seconds: number | null;
  actual_pace_min_per_km: number | null;
  actual_elevation_m: number | null;
  average_heart_rate: number | null;
  max_heart_rate: number | null;
  workout_type: string | null;
  notes: string | null;
  performance_score: number | null;
  planned_workout_id: number | null;
  created_at: string;
}

export interface WorkoutStats {
  total_workouts: number;
  total_distance_km: number;
  average_pace: number | null;
  workouts_by_type: Record<string, number>;
  weekly_distances: { week: string; distance_km: number }[];
}

export interface PlannedWorkout {
  id: number;
  plan_id: number;
  week_number: number;
  day_of_week: number;
  workout_type: string;
  target_distance_km: number | null;
  target_duration_minutes: number | null;
  target_pace_min_per_km: number | null;
  scheduled_date: string | null;
  calendar_event_id: string | null;
  completed: boolean;
  flexible: boolean;
  notes: string | null;
}

export interface TrainingPlan {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  start_date: string;
  end_date: string;
  status: string;
  current_week_number: number;
  goal_race_name: string | null;
  goal_race_date: string | null;
  goal_distance_km: number | null;
  workouts: PlannedWorkout[];
  created_at: string;
}

export interface UserPreferences {
  preferred_workout_days: string | null;
  preferred_workout_time: string;
  available_equipment: string | null;
  injury_history: string | null;
  sleep_hours_target: number | null;
}

export interface IntegrationStatus {
  strava_connected: boolean;
  google_connected: boolean;
  whoop_connected: boolean;
}
