import { Activity, Heart, Calendar, Zap } from 'lucide-react';
import { buildOAuthAuthorizeUrl } from '../lib/oauth';

export function LandingPage() {
  const connectUrl = buildOAuthAuthorizeUrl('strava', '/integrations');

  return (
    <div className="min-h-screen bg-grunge-black flex flex-col items-center justify-center px-6 text-center">
      <div className="max-w-2xl space-y-8">
        <h1 className="text-5xl font-black text-grunge-acid tracking-tight">
          SALTY PICKLE
        </h1>
        <p className="text-xl text-gray-300">
          AI-powered training plans that adapt to your body. Connect Strava,
          Whoop, and Google Calendar — and let the plan come to you.
        </p>

        <div className="grid grid-cols-2 gap-4 text-left max-w-md mx-auto">
          <Feature icon={<Activity className="w-5 h-5" />} text="Strava sync" />
          <Feature icon={<Heart className="w-5 h-5" />} text="Whoop recovery" />
          <Feature icon={<Calendar className="w-5 h-5" />} text="Calendar push" />
          <Feature icon={<Zap className="w-5 h-5" />} text="AI plan gen" />
        </div>

        <a
          href={connectUrl}
          className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-grunge-acid text-grunge-black font-bold text-lg hover:brightness-110 transition"
        >
          <Activity className="w-6 h-6" />
          Connect with Strava
        </a>

        <p className="text-sm text-gray-500">
          By signing in you agree to our{' '}
          <a href="/terms" className="underline hover:text-gray-300">
            Terms of Service
          </a>
          {' '}and{' '}
          <a href="/privacy" className="underline hover:text-gray-300">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
}

function Feature({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2 text-gray-400">
      {icon}
      <span className="text-sm">{text}</span>
    </div>
  );
}
