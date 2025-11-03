import { useEffect } from 'react';
import { telegramService } from './services/telegram';

function App() {
  useEffect(() => {
    // Initialize Telegram WebApp
    telegramService.init();

    // Get user data for debugging
    const userData = telegramService.getUserData();
    console.log('Telegram User Data:', userData);
  }, []);

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark font-display">
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-lg p-8 text-center max-w-md w-full">
          <h1 className="text-3xl font-bold text-[#191510] dark:text-background-light mb-4">
            Avito Tasker
          </h1>
          <p className="text-text-muted dark:text-text-muted-dark mb-6">
            Telegram Mini App инициализирован успешно!
          </p>
          <div className="flex items-center justify-center gap-2 text-primary">
            <span className="material-symbols-outlined text-4xl">
              checklist
            </span>
            <span className="text-lg font-semibold">
              Блоки 1-2 завершены
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
