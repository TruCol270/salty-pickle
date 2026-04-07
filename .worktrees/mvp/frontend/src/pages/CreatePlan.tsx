import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Flag, Calendar, MapPin, Target, Loader2 } from 'lucide-react';

interface RaceFormData {
  race_name: string;
  race_date: string;
  race_distance_km: number;
  current_fitness_level: string;
  weekly_mileage_km: number;
  years_experience: string;
}

export function CreatePlan() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<RaceFormData>({
    race_name: '',
    race_date: '',
    race_distance_km: 50,
    current_fitness_level: 'intermediate',
    weekly_mileage_km: 30,
    years_experience: '3-5',
  });

  const createPlan = useMutation({
    mutationFn: async (data: RaceFormData) => {
      const response = await axios.post('/api/v1/plans/ai-generate', data);
      return response.data;
    },
    onSuccess: (data) => {
      navigate(`/plans/${data.plan_id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createPlan.mutate(formData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-3 bg-indigo-100 rounded-xl">
              <Flag className="w-8 h-8 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Create Training Plan</h1>
              <p className="text-gray-500">Tell us about your goal race</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Race Name
                </label>
                <input
                  type="text"
                  value={formData.race_name}
                  onChange={(e) => setFormData({ ...formData, race_name: e.target.value })}
                  placeholder="e.g., UTMB, Western States, Boston Marathon"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  Race Date
                </label>
                <input
                  type="date"
                  value={formData.race_date}
                  onChange={(e) => setFormData({ ...formData, race_date: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPin className="w-4 h-4 inline mr-1" />
                  Race Distance (km)
                </label>
                <select
                  value={formData.race_distance_km}
                  onChange={(e) => setFormData({ ...formData, race_distance_km: Number(e.target.value) })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value={21.1}>Half Marathon (21.1km)</option>
                  <option value={42.2}>Marathon (42.2km)</option>
                  <option value={50}>50K</option>
                  <option value={80}>50 Miles</option>
                  <option value={100}>100K</option>
                  <option value={161}>100 Miles</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Target className="w-4 h-4 inline mr-1" />
                  Current Fitness Level
                </label>
                <select
                  value={formData.current_fitness_level}
                  onChange={(e) => setFormData({ ...formData, current_fitness_level: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="beginner">Beginner (just starting)</option>
                  <option value="intermediate">Intermediate (regular runner)</option>
                  <option value="advanced">Advanced (competitive)</option>
                  <option value="elite">Elite (professional)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Weekly Mileage (km)
                </label>
                <input
                  type="number"
                  value={formData.weekly_mileage_km}
                  onChange={(e) => setFormData({ ...formData, weekly_mileage_km: Number(e.target.value) })}
                  min={0}
                  max={200}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Years of Running Experience
                </label>
                <select
                  value={formData.years_experience}
                  onChange={(e) => setFormData({ ...formData, years_experience: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="0-1">Less than 1 year</option>
                  <option value="1-2">1-2 years</option>
                  <option value="3-5">3-5 years</option>
                  <option value="5-10">5-10 years</option>
                  <option value="10+">10+ years</option>
                </select>
              </div>
            </div>

            <div className="bg-indigo-50 rounded-lg p-4 text-sm text-indigo-800">
              <p>
                <strong>How it works:</strong> We'll analyze your Strava history, generate a personalized
                training plan using AI, and automatically sync workouts to your Google Calendar.
                The plan will adapt based on your actual performance.
              </p>
            </div>

            <button
              type="submit"
              disabled={createPlan.isPending}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-4 px-6 rounded-lg font-semibold transition-colors disabled:opacity-50"
            >
              {createPlan.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating Your Plan...
                </>
              ) : (
                <>
                  <Target className="w-5 h-5" />
                  Generate Training Plan
                </>
              )}
            </button>

            {createPlan.isError && (
              <div className="bg-red-50 text-red-600 p-4 rounded-lg text-sm">
                Failed to generate plan. Please try again.
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
