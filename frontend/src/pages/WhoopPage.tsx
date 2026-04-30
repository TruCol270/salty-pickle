import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Heart, Battery, Moon, Activity, TrendingUp, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../lib/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { requestOAuthAuthorizeUrl } from '../lib/oauth';
import type { WhoopRecoveryPoint } from '../types';

interface RecoveryData {
  connected: boolean;
  message?: string;
  recovery?: {
    id?: string;
    date?: string;
    recovery_score: number;
    resting_heart_rate: number;
    hrv_rmssd_milli: number;
  };
  recommendation?: string;
}

function getRecoveryColor(score: number): string {
  if (score < 40) return 'text-red-600';
  if (score < 70) return 'text-yellow-600';
  return 'text-green-600';
}

function getRecoveryBgColor(score: number): string {
  if (score < 40) return 'bg-red-100';
  if (score < 70) return 'bg-yellow-100';
  return 'bg-green-100';
}

function getRecoveryLabel(score: number): string {
  if (score < 40) return 'Low';
  if (score < 70) return 'Moderate';
  return 'Optimal';
}

function RecommendationBadge({ recommendation }: { recommendation: string }) {
  const config: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    push: { bg: 'bg-red-100', text: 'text-red-700', icon: <Activity className="w-4 h-4" /> },
    maintain: { bg: 'bg-blue-100', text: 'text-blue-700', icon: <TrendingUp className="w-4 h-4" /> },
    easy: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: <Moon className="w-4 h-4" /> },
    rest: { bg: 'bg-gray-100', text: 'text-gray-700', icon: <AlertCircle className="w-4 h-4" /> },
  };

  const c = config[recommendation] || config.rest;

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${c.bg} ${c.text}`}>
      {c.icon}
      <span className="capitalize">{recommendation}</span>
    </span>
  );
}

export function WhoopPage() {
  const [connectError, setConnectError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const beginWhoopConnect = async () => {
    setConnectError(null);
    setIsConnecting(true);
    try {
      const authUrl = await requestOAuthAuthorizeUrl('whoop', '/whoop');
      window.location.assign(authUrl);
    } catch (e) {
      const msg =
        e && typeof e === 'object' && 'message' in e
          ? String((e as { message?: string }).message)
          : 'Could not start Whoop OAuth flow';
      setConnectError(msg);
      setIsConnecting(false);
    }
  };

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery<RecoveryData>({
    queryKey: ['whoop-recovery'],
    queryFn: async () => {
      const response = await api.get<RecoveryData>('/api/v1/whoop/recovery');
      return response.data;
    },
    retry: false,
  });

  const { data: trendData } = useQuery<{ connected: boolean; points: WhoopRecoveryPoint[] }>({
    queryKey: ['whoop-recovery-trend'],
    queryFn: async () => {
      const response = await api.get('/api/v1/whoop/recovery/trend?days=7');
      return response.data;
    },
    enabled: data?.connected === true,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError) {
    const msg =
      error && typeof error === 'object' && 'message' in error
        ? String((error as { message?: string }).message)
        : 'Failed to load Whoop data';
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
        {msg}
      </div>
    );
  }

  if (!data?.connected) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Whoop Recovery</h1>
        {connectError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
            {connectError}
          </div>
        )}
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connect Whoop</h2>
          <p className="text-gray-500 mb-6">
            {data?.message || 'Link your Whoop account to track recovery and get personalized training recommendations.'}
          </p>
          <button
            type="button"
            onClick={() => void beginWhoopConnect()}
            disabled={isConnecting}
            className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 disabled:opacity-70 text-white rounded-lg font-medium transition-colors"
          >
            <Heart className="w-5 h-5" />
            {isConnecting ? 'Redirecting...' : 'Connect Whoop'}
          </button>
        </div>
      </div>
    );
  }

  const recovery = data.recovery;
  const rawScore = recovery?.recovery_score ?? 0;
  const scorePct = rawScore <= 1 ? rawScore * 100 : rawScore;

  const chartPoints =
    trendData?.points?.length && trendData.points.length > 0
      ? trendData.points
      : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Whoop Recovery</h1>
        <button
          type="button"
          onClick={() => void beginWhoopConnect()}
          disabled={isConnecting}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-70 text-white rounded-lg font-medium transition-colors"
        >
          <Heart className="w-4 h-4" />
          {isConnecting ? 'Redirecting...' : 'Reconnect'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Today&apos;s Recovery</h2>
          <div className="flex flex-col items-center">
            <div className={`relative w-40 h-40 rounded-full flex items-center justify-center ${getRecoveryBgColor(scorePct)}`}>
              <div className="text-center z-10">
                <p className={`text-5xl font-bold ${getRecoveryColor(scorePct)}`}>
                  {Math.round(scorePct)}
                </p>
                <p className="text-sm text-gray-600">%</p>
              </div>
              <svg className="absolute inset-0 w-full h-full -rotate-90 pointer-events-none">
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  className="text-gray-200"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  strokeDasharray={`${(scorePct / 100) * 440} 440`}
                  strokeLinecap="round"
                  className={getRecoveryColor(scorePct)}
                />
              </svg>
            </div>
            <p className={`mt-4 text-lg font-semibold ${getRecoveryColor(scorePct)}`}>
              {getRecoveryLabel(scorePct)}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Today&apos;s Recommendation</h2>
          <div className="h-40 flex items-center justify-center">
            {data.recommendation ? (
              <RecommendationBadge recommendation={data.recommendation} />
            ) : (
              <p className="text-gray-400">No recommendation</p>
            )}
          </div>
          <p className="text-sm text-gray-500 text-center mt-2">
            Based on your recovery score
          </p>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Battery className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">HRV</p>
                <p className="text-xl font-semibold">{recovery?.hrv_rmssd_milli ?? '--'} ms</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-pink-100 rounded-lg">
                <Heart className="w-5 h-5 text-pink-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Resting HR</p>
                <p className="text-xl font-semibold">{recovery?.resting_heart_rate ?? '--'} bpm</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-gray-500" />
          7-Day Trends
        </h2>
        {chartPoints.length === 0 ? (
          <p className="text-gray-500 text-sm py-8 text-center">
            Not enough recovery history yet. Check back after Whoop syncs a few cycles.
          </p>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartPoints}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis yAxisId="left" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
                />
                <Line yAxisId="left" type="monotone" dataKey="recovery" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e' }} name="Recovery %" />
                <Line yAxisId="right" type="monotone" dataKey="hrv" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} name="HRV (ms)" />
                <Line yAxisId="right" type="monotone" dataKey="rhr" stroke="#ec4899" strokeWidth={2} dot={{ fill: '#ec4899' }} name="RHR (bpm)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
