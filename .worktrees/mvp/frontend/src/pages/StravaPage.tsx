import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import { Activity, MapPin, Clock, Zap, TrendingUp } from 'lucide-react';
import { api } from '../lib/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

interface Workout {
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

interface WorkoutStats {
  total_workouts: number;
  total_distance_km: number;
  average_pace: number | null;
  workouts_by_type: Record<string, number>;
  weekly_distances: { week: string; distance_km: number }[];
}

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function StravaPage() {
  const {
    data: workouts,
    isLoading: workoutsLoading,
    isError: workoutsError,
  } = useQuery<Workout[]>({
    queryKey: ['strava-workouts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/workouts?limit=50');
      return response.data;
    },
    retry: false,
  });

  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
  } = useQuery<WorkoutStats>({
    queryKey: ['strava-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analytics/performance');
      return response.data;
    },
    retry: false,
  });

  if (workoutsLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (workoutsError || statsError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
        Could not load Strava or analytics data. Check that the API is running and you are signed in.
      </div>
    );
  }

  const pieData = stats?.workouts_by_type ? Object.entries(stats.workouts_by_type).map(([name, value]) => ({ name, value })) : [];
  const recentWorkouts = workouts?.slice(0, 10) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Strava Workouts</h1>
        <a
          href="/api/v1/auth/strava"
          className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors"
        >
          <Activity className="w-4 h-4" />
          Connect Strava
        </a>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Activity className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Workouts</p>
              <p className="text-xl font-semibold">{stats?.total_workouts || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MapPin className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Distance</p>
              <p className="text-xl font-semibold">{stats?.total_distance_km?.toFixed(1) || 0} km</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Clock className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Pace</p>
              <p className="text-xl font-semibold">
                {stats?.average_pace ? `${stats.average_pace.toFixed(1)} min/km` : '--'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Zap className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">This Month</p>
              <p className="text-xl font-semibold">
                {stats?.weekly_distances?.slice(-1)[0]?.distance_km?.toFixed(1) || 0} km
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-500" />
            Weekly Distance
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.weekly_distances || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="week" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
                  formatter={(value: number) => [`${value.toFixed(1)} km`, 'Distance']}
                />
                <Bar dataKey="distance_km" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Workouts by Type</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Workouts</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Date</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Workout</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Type</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Distance</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Duration</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Pace</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">HR</th>
              </tr>
            </thead>
            <tbody>
              {recentWorkouts.map((workout) => (
                <tr key={workout.id} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm">
                    {new Date(workout.start_time).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-sm font-medium">{workout.name}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700 capitalize">
                      {workout.workout_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-right">{workout.distance_km?.toFixed(1)} km</td>
                  <td className="py-3 px-4 text-sm text-right">{workout.duration_minutes} min</td>
                  <td className="py-3 px-4 text-sm text-right">
                    {workout.avg_pace_min_per_km ? `${workout.avg_pace_min_per_km.toFixed(1)}` : '--'}
                  </td>
                  <td className="py-3 px-4 text-sm text-right">
                    {workout.avg_heartrate || '--'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
