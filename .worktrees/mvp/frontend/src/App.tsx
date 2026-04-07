import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import { PlanEditor } from './pages/PlanEditor';
import { CreatePlan } from './pages/CreatePlan';
import { PreferencesPage } from './pages/PreferencesPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreatePlan />} />
          <Route path="/preferences" element={<PreferencesPage />} />
          <Route path="/plans/:id" element={<PlanEditor />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
