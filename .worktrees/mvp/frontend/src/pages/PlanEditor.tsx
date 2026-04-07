import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { format, differenceInDays } from 'date-fns';

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

  const { data: plan, isLoading } = useQuery<Plan>({
    queryKey: ['plan', id],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/plans/${id}`);
      return response.data;
    },
  });

  if (isLoading) return <div className="p-8">Loading...</div>;
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
          <button className="px-4 py-2 bg-blue-500 text-white rounded-lg">
            Sync to Calendar
          </button>
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
