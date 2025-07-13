import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import TermsGate from './components/TermsGate';
import LoadingSpinner from './components/LoadingSpinner';

// Pages
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Editor from './pages/Editor';
import Generator from './pages/Generator';
import Scheduler from './pages/Scheduler';
import Analytics from './pages/Analytics';
import Billing from './pages/Billing';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useSubscription } from './hooks/useSubscription';

// Utils
import { api } from './utils/api';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [hasAgreedToTerms, setHasAgreedToTerms] = useState(false);
  const { user, login, logout, isAuthenticated } = useAuth();
  const { subscription, loading: subscriptionLoading } = useSubscription();

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Check if user has agreed to terms
        if (isAuthenticated) {
          const response = await api.get('/auth/has-agreed');
          setHasAgreedToTerms(response.data.agreed);
        }
      } catch (error) {
        console.error('App initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeApp();
  }, [isAuthenticated]);

  // Show loading spinner while initializing
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Show terms gate if user hasn't agreed
  if (isAuthenticated && !hasAgreedToTerms) {
    return (
      <TermsGate onAgreed={() => setHasAgreedToTerms(true)} />
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-900 text-white">
          <AnimatePresence mode="wait">
            {isAuthenticated ? (
              <motion.div
                key="authenticated"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex"
              >
                <Sidebar />
                <div className="flex-1 flex flex-col">
                  <Navbar user={user} subscription={subscription} onLogout={logout} />
                  <main className="flex-1 p-6">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/upload" element={<Upload />} />
                      <Route path="/editor" element={<Editor />} />
                      <Route path="/generator" element={<Generator />} />
                      <Route path="/scheduler" element={<Scheduler />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/billing" element={<Billing />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </main>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="unauthenticated"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900"
              >
                <Routes>
                  <Route path="/login" element={<Login onLogin={login} />} />
                  <Route path="/register" element={<Register onRegister={login} />} />
                  <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Router>
      
      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#fff',
            border: '1px solid #374151',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App; 