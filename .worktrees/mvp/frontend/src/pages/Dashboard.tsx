import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Calendar, TrendingUp, Activity, Plus, Flag } from 'lucide-react';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { api } from '../lib/api';

interface PlanProgress {
  plan_name: string;
  current_week: number;
  total_weeks: number;
  completion_percentage: number;
  completed_distance_km: number;
  planned_distance_km: number;
}

interface PerformanceMetrics {
  total_workouts: number;
  total_distance_km: number;
  average_pace: number | null;
  workouts_by_type: Record<string, number>;
  weekly_distances: { week: string; distance_km: number }[];
}

export function Dashboard() {
  const { data: planProgress, isLoading: planLoading, isError: planError } = useQuery<PlanProgress>({
    queryKey: ['planProgress'],
    queryFn: async () => {
      const response = await api.get('/api/v1/plans/active');
      const planId = response.data.id;
      const progress = await api.get(`/api/v1/analytics/plan-progress/${planId}`);
      return progress.data;
    },
    retry: false,
  });

  const { data: performance, isLoading: perfLoading, isError: perfError } = useQuery<PerformanceMetrics>({
    queryKey: ['performance'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analytics/performance');
      return response.data;
    },
    retry: false,
  });

  if (planLoading || perfLoading) {
    return <div className="p-8 flex items-center justify-center"><LoadingSpinner size="lg" /></div>;
  }

  if (planError || perfError) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Dashboard</h2>
          <p className="text-red-700">Unable to load dashboard data. Please try refreshing the page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Training Dashboard</h1>
        <Link
          to="/create"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create New Plan
        </Link>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <Calendar className="w-10 h-10 text-blue-500" />
            <div>
              <p className="text-sm text-gray-500">Current Plan</p>
              <p className="text-xl font-semibold">{planProgress?.plan_name || 'No active plan'}</p>
              <p className="text-sm text-gray-500">
                Week {planProgress?.current_week || 0} of {planProgress?.total_weeks || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <Activity className="w-10 h-10 text-green-500" />
            <div>
              <p className="text-sm text-gray-500">Distance</p>
              <p className="text-xl font-semibold">
                {planProgress?.completed_distance_km || 0} km
              </p>
              <p className="text-sm text-gray-500">
                of {planProgress?.planned_distance_km || 0} km planned
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <TrendingUp className="w-10 h-10 text-purple-500" />
            <div>
              <p className="text-sm text-gray-500">Completion</p>
              <p className="text-xl font-semibold">
                {planProgress?.completion_percentage || 0}%
              </p>
              <p className="text-sm text-gray-500">
                {performance?.total_workouts || 0} workouts this month
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Weekly Distance</h2>
          <div className="h-48 flex items-end gap-2">
            {(performance?.weekly_distances || []).map((week, i) => (
              <div 
                key={i} 
                className="flex-1 bg-blue-500 rounded-t" 
                style={{ height: `${Math.min(week.distance_km * 4, 100)}%` }}
              >
                <p className="text-xs text-center mt-2">{week.distance_km}km</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Workouts by Type</h2>
          <div className="space-y-2">
            {Object.entries(performance?.workouts_by_type || {}).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="capitalize">{type}</span>
                <span className="font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
