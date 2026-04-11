import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { format, differenceInDays } from 'date-fns';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { TrainingPlan } from '../types';

export function PlanEditor() {
  const { id } = useParams<{ id: string }>();
  const [syncStatus, setSyncStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const { data: plan, isLoading, isError } = useQuery<TrainingPlan>({
    queryKey: ['plan', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/plans/${id}`);
      return response.data;
    },
  });

  const syncCalendar = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/api/v1/calendar/sync?plan_id=${id}`);
      return response.data;
    },
    onSuccess: (data) => {
      setSyncStatus({ type: 'success', message: `Synced ${data.synced_count} workouts to Google Calendar` });
    },
    onError: (err: { message: string }) => {
      setSyncStatus({ type: 'error', message: err.message || 'Failed to sync to calendar' });
    },
  });

  if (isLoading) return <LoadingSpinner size="lg" className="min-h-screen" />;
  if (isError || !plan) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
        <div className="bg-white rounded-lg shadow p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Plan not found</h2>
          <p className="text-gray-500">Unable to load this training plan.</p>
        </div>
      </div>
    );
  }

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
          <button
            onClick={() => { setSyncStatus(null); syncCalendar.mutate(); }}
            disabled={syncCalendar.isPending}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg disabled:opacity-50 transition-colors"
          >
            {syncCalendar.isPending ? 'Syncing...' : 'Sync to Calendar'}
          </button>
        </div>

        {syncStatus && (
          <div className={`mb-4 p-3 rounded-lg text-sm ${
            syncStatus.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {syncStatus.message}
          </div>
        )}

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
