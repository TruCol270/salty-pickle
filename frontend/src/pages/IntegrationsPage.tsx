import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { isAxiosError } from 'axios';
import { Activity, Calendar, Heart, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

import { api } from '../lib/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { buildOAuthAuthorizeUrl, requestOAuthAuthorizeUrl } from '../lib/oauth';
import type { IntegrationStatus } from '../types';

interface IntegrationCardProps {
  name: string;
  description: string;
  connected: boolean;
  icon: React.ReactNode;
  connectHref?: string;
  onConnect?: () => void;
  isConnecting?: boolean;
  color: string;
  details?: string | null;
}

function IntegrationCard({
  name,
  description,
  connected,
  icon,
  connectHref,
  onConnect,
  isConnecting,
  color,
  details,
}: IntegrationCardProps) {
  const className = `inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
    connected
      ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
      : 'bg-indigo-600 hover:bg-indigo-700 text-white'
  }`;

  const label = connected ? 'Reconnect' : 'Connect';

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
      
      {onConnect ? (
        <button
          type="button"
          onClick={onConnect}
          disabled={isConnecting}
          className={`${className} disabled:opacity-70 disabled:cursor-not-allowed`}
        >
          {isConnecting ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Redirecting...
            </>
          ) : (
            <>
              <Activity className="w-4 h-4" />
              {label}
            </>
          )}
        </button>
      ) : (
        <a href={connectHref ?? '#'} className={className}>
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
      )}
    </div>
  );
}

export function IntegrationsPage() {
  const connectStravaUrl = buildOAuthAuthorizeUrl('strava', '/integrations');
  const [connectingProvider, setConnectingProvider] = useState<'google' | 'whoop' | null>(null);
  const [connectError, setConnectError] = useState<string | null>(null);

  const beginAuthenticatedConnect = async (provider: 'google' | 'whoop') => {
    setConnectError(null);
    setConnectingProvider(provider);
    try {
      const authUrl = await requestOAuthAuthorizeUrl(provider, '/integrations');
      window.location.assign(authUrl);
    } catch (e) {
      const message = isAxiosError(e)
        ? e.response?.data?.error?.message ?? e.message
        : 'Could not start OAuth flow';
      setConnectError(message);
      setConnectingProvider(null);
    }
  };

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
      {connectError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {connectError}
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
          connectHref={connectStravaUrl}
          icon={<Activity className="w-6 h-6 text-orange-600" />}
          color="bg-orange-100"
          details={data?.strava.athlete_id}
        />

        <IntegrationCard
          name="Google Calendar"
          description="Push training workouts to your calendar"
          connected={data?.google.connected ?? false}
          onConnect={() => void beginAuthenticatedConnect('google')}
          isConnecting={connectingProvider === 'google'}
          icon={<Calendar className="w-6 h-6 text-blue-600" />}
          color="bg-blue-100"
          details={data?.google.calendar_id}
        />

        <IntegrationCard
          name="Whoop"
          description="Track recovery and get smart recommendations"
          connected={data?.whoop.connected ?? false}
          onConnect={() => void beginAuthenticatedConnect('whoop')}
          isConnecting={connectingProvider === 'whoop'}
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
