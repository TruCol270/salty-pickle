import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { format, differenceInDays } from 'date-fns';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { api } from '../lib/api';
import { useState } from 'react';

interface Workout {
  id: number;
  week_number: number;
  day_of_week: number;
  workout_type: string;
  target_distance_km: number | null;
  scheduled_date: string;
  completed: boolean;
}

interface Plan {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  workouts: Workout[];
}

export function PlanEditor() {
  const { id } = useParams<{ id: string }>();

  const { data: plan, isLoading, isError } = useQuery<Plan>({
    queryKey: ['plan', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/plans/${id}`);
      return response.data;
    },
  });

  const [syncFeedback, setSyncFeedback] = useState<{ status: 'idle' | 'loading' | 'success' | 'error'; message?: string }>({ status: 'idle' });

  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/api/v1/calendar/sync`, { plan_id: id });
      return response.data;
    },
    onSuccess: () => {
      setSyncFeedback({ status: 'success', message: 'Synced to calendar successfully!' });
      setTimeout(() => setSyncFeedback({ status: 'idle' }), 3000);
    },
    onError: () => {
      setSyncFeedback({ status: 'error', message: 'Failed to sync to calendar' });
      setTimeout(() => setSyncFeedback({ status: 'idle' }), 3000);
    },
  });

  if (isLoading) return <div className="p-8 flex items-center justify-center"><LoadingSpinner size="lg" /></div>;
  if (isError) return (
    <div className="p-8">
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Plan</h2>
        <p className="text-red-700">Unable to load the training plan. Please try refreshing the page.</p>
      </div>
    </div>
  );
  if (!plan) return <div className="p-8">Plan not found</div>;

  const weeks = Math.ceil(differenceInDays(new Date(plan.end_date), new Date(plan.start_date)) / 7);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">{plan.name}</h1>
            <p className="text-gray-500">
              {format(new Date(plan.start_date), 'MMM d, yyyy')} - {format(new Date(plan.end_date), 'MMM d, yyyy')}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              {syncMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" />
                  Syncing...
                </>
              ) : (
                'Sync to Calendar'
              )}
            </button>
            {syncFeedback.status !== 'idle' && (
              <p className={`text-sm ${syncFeedback.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                {syncFeedback.message}
              </p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-3 text-left">Week</th>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                  <th key={day} className="px-4 py-3 text-left">{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: weeks }, (_, weekNum) => (
                <tr key={weekNum} className="border-t">
                  <td className="px-4 py-3 font-medium">Week {weekNum + 1}</td>
                  {[0, 1, 2, 3, 4, 5, 6].map((day) => {
                    const workout = plan.workouts.find(
                      (w) => w.week_number === weekNum + 1 && w.day_of_week === day
                    );
                    return (
                      <td key={day} className="px-4 py-3">
                        {workout ? (
                          <div className={`p-2 rounded text-sm ${workout.completed ? 'bg-green-100 text-green-800' : 'bg-blue-50 text-blue-800'}`}>
                            <div className="font-medium capitalize">{workout.workout_type}</div>
                            {workout.target_distance_km && (
                              <div className="text-xs">{workout.target_distance_km}km</div>
                            )}
                          </div>
                        ) : (
                          <div className="text-gray-300 text-sm">-</div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
