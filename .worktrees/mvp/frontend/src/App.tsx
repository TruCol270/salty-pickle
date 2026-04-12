import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Dashboard } from './pages/Dashboard';
import { PlanEditor } from './pages/PlanEditor';
import { CreatePlan } from './pages/CreatePlan';
import { PreferencesPage } from './pages/PreferencesPage';
import { StravaPage } from './pages/StravaPage';
import { WhoopPage } from './pages/WhoopPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { LandingPage } from './pages/LandingPage';
import type { ReactNode } from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ErrorBoundary>
            <Routes>
              <Route path="/login" element={<LandingPage />} />
              <Route
                element={
                  <RequireAuth>
                    <Layout />
                  </RequireAuth>
                }
              >
                <Route path="/" element={<Dashboard />} />
                <Route path="/strava" element={<StravaPage />} />
                <Route path="/whoop" element={<WhoopPage />} />
                <Route path="/plans/active" element={<PlanEditor />} />
                <Route path="/plans/:id" element={<PlanEditor />} />
                <Route path="/integrations" element={<IntegrationsPage />} />
                <Route path="/create" element={<CreatePlan />} />
                <Route path="/preferences" element={<PreferencesPage />} />
              </Route>
            </Routes>
          </ErrorBoundary>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
