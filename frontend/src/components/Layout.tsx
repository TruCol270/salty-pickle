import { Outlet } from 'react-router-dom';
import { FeedbackButton } from './FeedbackButton';
import { Navigation } from './Navigation';

export function Layout() {
  return (
    <div className="relative z-10 flex min-h-screen bg-grunge-black">
      <Navigation />
      <main className="flex-1 overflow-auto px-4 py-6 md:px-8">
        <div className="mx-auto max-w-7xl">
          <Outlet />
          <FeedbackButton />
        </div>
      </main>
    </div>
  );
}
