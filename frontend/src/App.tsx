import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { JobSubmit } from './pages/JobSubmit';
import { JobList } from './pages/JobList';
import { JobDetail } from './pages/JobDetail';
import { ModelsPage } from './pages/ModelsPage';
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="jobs/new" element={<JobSubmit />} />
            <Route path="jobs" element={<JobList />} />
            <Route path="jobs/:jobId" element={<JobDetail />} />
            <Route path="models" element={<ModelsPage />} />
          </Route>
        </Routes>
        <ReactQueryDevtools initialIsOpen={false} />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;