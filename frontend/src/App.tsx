import { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { telegramService } from './services/telegram';
import { apiService } from './services/api';
import { NotificationProvider } from './hooks/useNotification';
import { logger } from './utils/logger';
import { Home } from './pages/Home';
import { TasksPage } from './pages/TasksPage';
import { TaskDetailPage } from './pages/TaskDetailPage';
import { ReferralsPage } from './pages/ReferralsPage';
import { ErrorBoundary } from './components/ErrorBoundary';

const MAX_RETRIES = 3;
const RETRY_DELAY = 2000; // 2 seconds (improved from 1s)

function App() {
  const [isInitializing, setIsInitializing] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [shouldRetry, setShouldRetry] = useState(false);

  const initializeApp = useCallback(async () => {
    console.log('[DIAG] ========================================');
    console.log('[DIAG] App.initializeApp() STARTED');
    console.log('[DIAG] Retry count:', retryCount);
    console.log('[DIAG] Timestamp:', new Date().toISOString());
    console.log('[DIAG] ========================================');

    try {
      setInitError(null);
      setShouldRetry(false);

      // Initialize Telegram WebApp
      console.log('[DIAG] Step 1: Calling telegramService.init()...');
      telegramService.init();
      console.log('[DIAG] Step 1: telegramService.init() completed');

      // Get user data for debugging (dev only)
      console.log('[DIAG] Step 2: Getting user data...');
      const userData = telegramService.getUserData();
      console.log('[DIAG] Step 2: User data:', userData ? `ID=${userData.telegram_id}` : 'null');

      if (import.meta.env.DEV) {
        logger.log('Telegram User Data:', userData);
      }

      // Initialize user in database - MUST complete before rendering pages
      console.log('[DIAG] Step 3: Calling apiService.initUser()...');
      console.log('[DIAG] Starting initUser at:', Date.now());

      const startTime = Date.now();
      await apiService.initUser();
      const endTime = Date.now();

      console.log('[DIAG] Step 3: initUser() completed in', (endTime - startTime), 'ms');
      logger.log('User initialized successfully');

      console.log('[DIAG] Step 4: Setting isInitializing = false');
      setIsInitializing(false);
      setRetryCount(0); // Reset on success

      console.log('[DIAG] ========================================');
      console.log('[DIAG] App.initializeApp() COMPLETED SUCCESS');
      console.log('[DIAG] ========================================');
    } catch (error) {
      console.error('[DIAG] ========================================');
      console.error('[DIAG] App.initializeApp() FAILED');
      console.error('[DIAG] Error:', error);
      console.error('[DIAG] Error type:', error instanceof Error ? error.constructor.name : typeof error);
      console.error('[DIAG] Error message:', error instanceof Error ? error.message : String(error));
      console.error('[DIAG] ========================================');

      logger.error('Failed to initialize user:', error);

      // Check if we can retry
      if (retryCount < MAX_RETRIES) {
        console.warn('[DIAG] Will retry. Current attempt:', retryCount + 1, '/', MAX_RETRIES);
        logger.warn(`Will retry initialization (attempt ${retryCount + 1}/${MAX_RETRIES})...`);
        setRetryCount(prev => prev + 1);
        setShouldRetry(true); // Trigger retry via useEffect
      } else {
        // Max retries reached - show error
        console.error('[DIAG] MAX RETRIES REACHED. Showing error to user.');
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setInitError(`Не удалось инициализировать приложение: ${errorMessage}`);
        setIsInitializing(false);
      }
    }
  }, [retryCount]); // Added retryCount as dependency for logging

  // Initial mount: start initialization
  useEffect(() => {
    initializeApp();
  }, [initializeApp]);

  // Retry logic: triggered by shouldRetry state change
  useEffect(() => {
    if (shouldRetry) {
      console.log('[DIAG] Retry scheduled in', RETRY_DELAY, 'ms...');
      const timeoutId = setTimeout(() => {
        console.log('[DIAG] Retry timeout fired. Calling initializeApp()...');
        logger.log(`Retrying initialization (attempt ${retryCount}/${MAX_RETRIES})...`);
        initializeApp();
      }, RETRY_DELAY);

      return () => {
        console.log('[DIAG] Retry timeout cleared');
        clearTimeout(timeoutId);
      };
    }
  }, [shouldRetry, retryCount, initializeApp]);

  const handleRetry = () => {
    setRetryCount(0);
    setIsInitializing(true);
    initializeApp();
  };

  // Show loading screen during initialization
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#1a1a1a] text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C9A87C] mx-auto mb-4"></div>
          <p className="text-lg">Загрузка...</p>
          {retryCount > 0 && (
            <p className="text-sm text-gray-400 mt-2">Попытка {retryCount}/{MAX_RETRIES}</p>
          )}
        </div>
      </div>
    );
  }

  // Show error screen with retry button
  if (initError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#1a1a1a] text-white px-4">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold mb-2">Ошибка инициализации</h2>
          <p className="text-gray-400 mb-6">{initError}</p>
          <button
            onClick={handleRetry}
            className="bg-[#C9A87C] text-black px-6 py-3 rounded-lg font-semibold hover:bg-[#b8976b] transition-colors"
          >
            Повторить попытку
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <NotificationProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/tasks/:assignmentId" element={<TaskDetailPage />} />
            <Route path="/referrals" element={<ReferralsPage />} />
          </Routes>
        </BrowserRouter>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;
