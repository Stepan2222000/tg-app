import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { telegramService } from './services/telegram';
import { NotificationProvider } from './hooks/useNotification';
import { Home } from './pages/Home';

function App() {
  useEffect(() => {
    // Initialize Telegram WebApp
    telegramService.init();

    // Get user data for debugging
    const userData = telegramService.getUserData();
    console.log('Telegram User Data:', userData);
  }, []);

  return (
    <NotificationProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          {/* Placeholder routes for future implementation */}
          <Route path="/tasks" element={<div>Tasks Page - Coming Soon</div>} />
          <Route path="/referrals" element={<div>Referrals Page - Coming Soon</div>} />
        </Routes>
      </BrowserRouter>
    </NotificationProvider>
  );
}

export default App;
