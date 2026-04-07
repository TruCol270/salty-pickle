import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Settings, Save, Loader2, ArrowLeft, Clock, Calendar, Moon, AlertCircle } from 'lucide-react';

interface Preferences {
  preferred_workout_days: string;
  preferred_workout_time: string;
  available_equipment: string;
  injury_history: string;
  sleep_hours_target: number | null;
}

const DAYS = [
  { value: '0', label: 'Mon' },
  { value: '1', label: 'Tue' },
  { value: '2', label: 'Wed' },
  { value: '3', label: 'Thu' },
  { value: '4', label: 'Fri' },
  { value: '5', label: 'Sat' },
  { value: '6', label: 'Sun' },
];

export function PreferencesPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<Preferences>({
    preferred_workout_days: '0,2,4,6',
    preferred_workout_time: 'morning',
    available_equipment: '',
    injury_history: '',
    sleep_hours_target: 7.5,
  });

  const { data: prefs, isLoading } = useQuery<Preferences>({
    queryKey: ['preferences'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/user/preferences');
      return response.data;
    },
  });

  useEffect(() => {
    if (prefs) {
      setFormData({
        preferred_workout_days: prefs.preferred_workout_days || '0,2,4,6',
        preferred_workout_time: prefs.preferred_workout_time || 'morning',
        available_equipment: prefs.available_equipment || '',
        injury_history: prefs.injury_history || '',
        sleep_hours_target: prefs.sleep_hours_target || 7.5,
      });
    }
  }, [prefs]);

  const updatePrefs = useMutation({
    mutationFn: async (data: Preferences) => {
      const response = await axios.put('/api/v1/user/preferences', data);
      return response.data;
    },
    onSuccess: () => {
      navigate('/create');
    },
  });

  const handleDayToggle = (day: string) => {
    const current = formData.preferred_workout_days.split(',').filter(d => d);
    if (current.includes(day)) {
      setFormData({
        ...formData,
        preferred_workout_days: current.filter(d => d !== day).join(','),
      });
    } else {
      setFormData({
        ...formData,
        preferred_workout_days: [...current, day].sort().join(','),
      });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updatePrefs.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex items-center gap-3 mb-8">
            <Link to="/create" className="p-3 bg-gray-100 rounded-xl hover:bg-gray-200">
              <ArrowLeft className="w-8 h-8 text-gray-600" />
            </Link>
            <div className="p-3 bg-indigo-100 rounded-xl">
              <Settings className="w-8 h-8 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Training Preferences</h1>
              <p className="text-gray-500">Customize your training plan</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                <Calendar className="w-4 h-4" />
                Preferred Workout Days
              </label>
              <div className="flex gap-2">
                {DAYS.map((day) => {
                  const isSelected = formData.preferred_workout_days.split(',').includes(day.value);
                  return (
                    <button
                      key={day.value}
                      type="button"
                      onClick={() => handleDayToggle(day.value)}
                      className={`w-12 h-12 rounded-lg font-medium transition-colors ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {day.label}
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Select the days you typically have time to workout
              </p>
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                <Clock className="w-4 h-4" />
                Preferred Workout Time
              </label>
              <div className="grid grid-cols-3 gap-3">
                {['morning', 'afternoon', 'evening'].map((time) => (
                  <button
                    key={time}
                    type="button"
                    onClick={() => setFormData({ ...formData, preferred_workout_time: time })}
                    className={`py-3 px-4 rounded-lg font-medium capitalize transition-colors ${
                      formData.preferred_workout_time === time
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {time}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Available Equipment
              </label>
              <input
                type="text"
                value={formData.available_equipment}
                onChange={(e) => setFormData({ ...formData, available_equipment: e.target.value })}
                placeholder="e.g., trail shoes, road shoes, treadmill, watch"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                List what running gear you have access to
              </p>
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <AlertCircle className="w-4 h-4" />
                Injury History
              </label>
              <textarea
                value={formData.injury_history}
                onChange={(e) => setFormData({ ...formData, injury_history: e.target.value })}
                placeholder="e.g., knee pain in 2023, Achilles issues"
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                We'll adjust your plan to avoid aggravating past injuries
              </p>
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Moon className="w-4 h-4" />
                Target Sleep Hours
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={5}
                  max={10}
                  step={0.5}
                  value={formData.sleep_hours_target || 7.5}
                  onChange={(e) => setFormData({ ...formData, sleep_hours_target: parseFloat(e.target.value) })}
                  className="flex-1"
                />
                <span className="text-lg font-semibold w-16 text-center">
                  {formData.sleep_hours_target || 7.5}h
                </span>
              </div>
            </div>

            <div className="bg-indigo-50 rounded-lg p-4 text-sm text-indigo-800">
              <p>
                <strong>Why we need this:</strong> Your preferences help us generate a training plan that fits
                your schedule and avoids workouts that could aggravate past injuries. We'll also use this
                when adjusting your plan based on recovery.
              </p>
            </div>

            <button
              type="submit"
              disabled={updatePrefs.isPending}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-4 px-6 rounded-lg font-semibold transition-colors disabled:opacity-50"
            >
              {updatePrefs.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Save & Continue
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
