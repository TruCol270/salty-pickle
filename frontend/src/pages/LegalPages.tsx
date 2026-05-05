export function TermsPage() {
  return (
    <LegalShell title="Terms of Service">
      <p>
        Salty Pickle is beta software for training planning support. It is not
        medical advice, coaching certification, or a guarantee of race outcomes.
      </p>
      <p>
        You are responsible for deciding whether workouts are appropriate for
        your health, conditions, terrain, and schedule. Stop using the service if
        it produces unsafe or unsuitable recommendations.
      </p>
      <p>
        Connected services may limit, change, or revoke access. We may change or
        discontinue beta features while the product is being refined.
      </p>
    </LegalShell>
  );
}

export function PrivacyPage() {
  return (
    <LegalShell title="Privacy Policy">
      <p>
        Salty Pickle uses account, training, recovery, and calendar data to sync
        workouts, generate plans, and show product analytics.
      </p>
      <p>
        OAuth tokens are used only to connect requested integrations. Production
        deployments should store secrets in the hosting provider and rotate them
        whenever access may have been exposed.
      </p>
      <p>
        Product analytics and error reporting can be enabled with PostHog and
        Sentry environment variables. Keep those providers configured without
        sensitive personal notes or raw tokens.
      </p>
    </LegalShell>
  );
}

function LegalShell({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-grunge-black px-6 py-12 text-gray-200">
      <article className="mx-auto max-w-3xl space-y-5">
        <a href="/login" className="text-sm font-semibold text-grunge-acid hover:underline">
          Salty Pickle
        </a>
        <h1 className="font-display text-4xl font-black text-white">{title}</h1>
        <div className="space-y-4 leading-7 text-gray-300">{children}</div>
      </article>
    </main>
  );
}
