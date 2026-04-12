import { useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Activity, Calendar, Heart, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

import { api } from '../lib/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useAuth } from '../context/AuthContext';
import type { IntegrationStatus } from '../types';

interface IntegrationCardProps {
  name: string;
  description: string;
  connected: boolean;
  icon: React.ReactNode;
  connectHref: string;
  color: string;
  details?: string;
}

function IntegrationCard({ name, description, connected, icon, connectHref, color, details }: IntegrationCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${color}`}>
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{name}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
        </div>
        {connected ? (
          <span className="flex items-center gap-1 text-green-600 text-sm font-medium">
            <CheckCircle className="w-4 h-4" />
            Connected
          </span>
        ) : (
          <span className="flex items-center gap-1 text-gray-400 text-sm font-medium">
            <XCircle className="w-4 h-4" />
            Not connected
          </span>
        )}
      </div>
      
      {details && connected && (
        <p className="text-xs text-gray-500 mb-4">ID: {details}</p>
      )}
      
      <a
        href={connectHref}
        className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
          connected
            ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            : 'bg-indigo-600 hover:bg-indigo-700 text-white'
        }`}
      >
        {connected ? (
          <>
            <RefreshCw className="w-4 h-4" />
            Reconnect
          </>
        ) : (
          <>
            <Activity className="w-4 h-4" />
            Connect
          </>
        )}
      </a>
    </div>
  );
}

export function IntegrationsPage() {
  const { userId } = useAuth();
  const oauthRedirect = new URLSearchParams({
    redirect_url: `${window.location.origin}/integrations`,
  });
  if (userId != null) {
    oauthRedirect.set('user_id', String(userId));
  }
  const oauthQuery = `?${oauthRedirect.toString()}`;

  const { data, isLoading, refetch, isError, error } = useQuery<IntegrationStatus>({
    queryKey: ['integrations'],
    queryFn: async () => {
      const response = await api.get('/api/v1/integrations');
      return response.data;
    },
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const unauthorizedStatus =
    isError && error && typeof error === 'object' && 'status' in error
      ? (error as { status?: number }).status
      : isAxiosError(error)
        ? error.response?.status
        : undefined;
  const isUnauthorized = isError && unauthorizedStatus === 401;

  return (
    <div className="space-y-6">
      {isUnauthorized && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Sign in required. Use Connect below to complete OAuth; you will be redirected back with a
          session, or set <code className="rounded bg-amber-100 px-1">access_token</code> via{' '}
          <code className="rounded bg-amber-100 px-1">POST /auth/token/bootstrap</code> when{' '}
          <code className="rounded bg-amber-100 px-1">AUTH_BOOTSTRAP_KEY</code> is configured.
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-gray-500">Connect your fitness accounts to sync data</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <RefreshCw className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <IntegrationCard
          name="Strava"
          description="Sync your workout history and activities"
          connected={data?.strava.connected ?? false}
          connectHref={`/auth/strava/authorize${oauthQuery}`}
          icon={<Activity className="w-6 h-6 text-orange-600" />}
          color="bg-orange-100"
          details={data?.strava.athlete_id}
        />

        <IntegrationCard
          name="Google Calendar"
          description="Push training workouts to your calendar"
          connected={data?.google.connected ?? false}
          connectHref={`/auth/google/authorize${oauthQuery}`}
          icon={<Calendar className="w-6 h-6 text-blue-600" />}
          color="bg-blue-100"
          details={data?.google.calendar_id}
        />

        <IntegrationCard
          name="Whoop"
          description="Track recovery and get smart recommendations"
          connected={data?.whoop.connected ?? false}
          connectHref={`/auth/whoop/authorize${oauthQuery}`}
          icon={<Heart className="w-6 h-6 text-red-600" />}
          color="bg-red-100"
          details={data?.whoop.user_id}
        />
      </div>

      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
        <p>
          <strong>Note:</strong> To disconnect an integration, visit the settings page of that service 
          and revoke access. For Strava, go to{' '}
          <a href="https://www.strava.com/settings/apps" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
            strava.com/settings/apps
          </a>
        </p>
      </div>
    </div>
  );
}
