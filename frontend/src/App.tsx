import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { telegramService } from './services/telegram';
import { apiService } from './services/api';
import { NotificationProvider } from './hooks/useNotification';
import { logger } from './utils/logger';
import { Home } from './pages/Home';
import { TasksPage } from './pages/TasksPage';
import { TaskDetailPage } from './pages/TaskDetailPage';
import { ReferralsPage } from './pages/ReferralsPage';

function App() {
  useEffect(() => {
    // Initialize Telegram WebApp
    telegramService.init();

    // Initialize user in database
    const initUser = async () => {
      try {
        await apiService.initUser();
        logger.log('User initialized successfully');
      } catch (error) {
        logger.error('Failed to initialize user:', error);
      }
    };

    initUser();

    // Get user data for debugging (dev only)
    if (import.meta.env.DEV) {
      const userData = telegramService.getUserData();
      logger.log('Telegram User Data:', userData);
    }
  }, []);

  return (
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
  );
}

export default App;
