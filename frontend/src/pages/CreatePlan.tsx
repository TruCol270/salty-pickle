import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Flag, Calendar, MapPin, Target, Loader2, Link as LinkIcon, Settings } from 'lucide-react';

interface RaceFormData {
  race_name: string;
  race_date: string;
  race_distance_km: number;
  current_fitness_level: string;
  weekly_mileage_km: number;
  years_experience: string;
  race_url?: string;
}

interface RaceAnalysis {
  race_info: {
    race_name: string;
    race_date: string;
    distance_km: number;
    elevation_gain_m: number;
    difficulty: string;
    location: string;
  };
  training_advice: {
    weekly_long_run_max_km: number;
    weekly_volume_cap_km: number;
    key_workouts: string[];
  };
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
    race_url: '',
  });

  const [raceAnalysis, setRaceAnalysis] = useState<RaceAnalysis | null>(null);
  const [analyzingUrl, setAnalyzingUrl] = useState(false);

  const analyzeUrl = useMutation({
    mutationFn: async (url: string) => {
      const response = await api.post(`/api/v1/races/analyze?url=${encodeURIComponent(url)}`);
      return response.data;
    },
    onSuccess: (data: RaceAnalysis) => {
      setRaceAnalysis(data);
      if (data.race_info.race_name) {
        setFormData(prev => ({ ...prev, race_name: data.race_info.race_name }));
      }
      if (data.race_info.distance_km) {
        setFormData(prev => ({ ...prev, race_distance_km: data.race_info.distance_km }));
      }
      if (data.race_info.race_date) {
        const date = new Date(data.race_info.race_date);
        setFormData(prev => ({ ...prev, race_date: date.toISOString().split('T')[0] }));
      }
    },
    onError: () => {
      setRaceAnalysis(null);
    },
  });

  const createPlan = useMutation({
    mutationFn: async (data: RaceFormData) => {
      const planData = {
        race_name: data.race_name,
        race_date: data.race_date ? `${data.race_date}T00:00:00` : null,
        race_distance_km: data.race_distance_km,
        current_fitness_level: data.current_fitness_level,
        weekly_mileage_km: data.weekly_mileage_km,
        years_experience: data.years_experience,
      };
      const response = await api.post('/api/v1/plans/ai-generate', planData);
      return response.data;
    },
    onSuccess: (data) => {
      navigate(`/plans/${data.plan_id}`);
    },
  });

  const handleAnalyzeUrl = () => {
    if (formData.race_url) {
      setAnalyzingUrl(true);
      analyzeUrl.mutate(formData.race_url);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createPlan.mutate(formData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-100 rounded-xl">
                <Flag className="w-8 h-8 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Create Training Plan</h1>
                <p className="text-gray-500">Tell us about your goal race</p>
              </div>
            </div>
            <Link
              to="/preferences"
              className="flex items-center gap-2 text-gray-500 hover:text-gray-700"
            >
              <Settings className="w-5 h-5" />
              <span className="text-sm">Preferences</span>
            </Link>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <label className="block text-sm font-medium text-blue-800 mb-2">
                <LinkIcon className="w-4 h-4 inline mr-1" />
                Have a race URL? Paste it here to auto-fill details
              </label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={formData.race_url || ''}
                  onChange={(e) => setFormData({ ...formData, race_url: e.target.value })}
                  placeholder="e.g., https://www.utmbmontblanc.com/en/utmb"
                  className="flex-1 px-4 py-3 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={handleAnalyzeUrl}
                  disabled={analyzingUrl || !formData.race_url}
                  className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
                >
                  {analyzingUrl ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
              {raceAnalysis && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm text-green-800 font-medium">
                    ✓ Found: {raceAnalysis.race_info.race_name} ({raceAnalysis.race_info.distance_km}km, {raceAnalysis.race_info.difficulty} difficulty)
                  </p>
                  {raceAnalysis.race_info.elevation_gain_m && (
                    <p className="text-xs text-green-700">
                      Elevation: {raceAnalysis.race_info.elevation_gain_m}m
                    </p>
                  )}
                </div>
              )}
            </div>

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
                Failed to generate plan. Please try again. (Check if OpenAI API key has quota)
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
