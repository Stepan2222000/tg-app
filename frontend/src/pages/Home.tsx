import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { formatCurrency } from '../utils/formatters';
import { Button } from '../components/ui/Button';
import { WithdrawalModal } from '../components/WithdrawalModal';
import { useNotification } from '../hooks/useNotification';
import type { User, Withdrawal } from '../types';

export function Home() {
  const navigate = useNavigate();
  const { showError } = useNotification();
  const [user, setUser] = useState<User | null>(null);
  const [pendingWithdrawal, setPendingWithdrawal] = useState<Withdrawal | null>(null);
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);
      const userData = await apiService.getUser();
      setUser(userData);

      // Проверяем есть ли pending withdrawal
      const history = await apiService.getWithdrawalHistory();
      const pending = history.find((w) => w.status === 'pending');
      setPendingWithdrawal(pending || null);
    } catch (error) {
      console.error('Failed to load user data:', error);
      showError(
        error instanceof Error
          ? error.message
          : 'Не удалось загрузить данные. Попробуйте обновить страницу.'
      );
    } finally {
      setLoading(false);
    }
  };

  const totalBalance = user ? user.main_balance + user.referral_balance : 0;

  const handleWithdrawalSuccess = () => {
    setIsWithdrawalModalOpen(false);
    loadUserData(); // Перезагружаем данные после успешной заявки
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <span className="material-symbols-outlined text-5xl text-primary animate-spin">
          progress_activity
        </span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark font-display">
      <div className="max-w-2xl mx-auto p-4 space-y-4">
        {/* Header */}
        <header className="text-center py-6">
          <h1 className="text-4xl font-black text-gray-900 dark:text-gray-100">
            Avito Tasker
          </h1>
        </header>

        {/* Balance Card */}
        <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-text-muted dark:text-text-muted-dark text-sm mb-2">
                Ваш баланс
              </p>
              <p className="text-5xl font-black text-gray-900 dark:text-gray-100">
                {formatCurrency(totalBalance)}
              </p>
              {pendingWithdrawal && (
                <p className="text-primary text-sm mt-2 font-medium">
                  В обработке: {formatCurrency(pendingWithdrawal.amount)}
                </p>
              )}
            </div>
            <Button onClick={() => setIsWithdrawalModalOpen(true)}>Вывести</Button>
          </div>
        </div>

        {/* Navigation Cards */}
        <div className="space-y-3">
          {/* Tasks Card */}
          <button
            onClick={() => navigate('/tasks')}
            className="w-full bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6 flex items-center gap-4 hover:shadow-lg transition-shadow"
          >
            <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-3xl">
                checklist
              </span>
            </div>
            <span className="flex-1 text-left text-xl font-bold text-gray-900 dark:text-gray-100">
              Работа с задачами
            </span>
            <span className="material-symbols-outlined text-gray-400 text-3xl">
              chevron_right
            </span>
          </button>

          {/* Referrals Card */}
          <button
            onClick={() => navigate('/referrals')}
            className="w-full bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6 flex items-center gap-4 hover:shadow-lg transition-shadow"
          >
            <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-3xl">
                group_add
              </span>
            </div>
            <span className="flex-1 text-left text-xl font-bold text-gray-900 dark:text-gray-100">
              Реферальная программа
            </span>
            <span className="material-symbols-outlined text-gray-400 text-3xl">
              chevron_right
            </span>
          </button>
        </div>

        {/* How It Works Section */}
        <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Как это работает?
          </h2>
          <p className="text-text-muted dark:text-text-muted-dark leading-relaxed">
            Выполняйте простые задачи по написанию сообщений на Авито и получайте за это
            вознаграждение. Каждое выполненное задание пополняет ваш баланс, который вы
            можете вывести в любое удобное время.
          </p>
        </div>

        {/* Support Button */}
        <button
          onClick={() =>
            window.open(import.meta.env.VITE_SUPPORT_URL || 'https://t.me/support', '_blank')
          }
          className="w-full bg-card-light dark:bg-card-dark rounded-xl shadow-md p-4 flex items-center justify-center gap-3 hover:shadow-lg transition-shadow"
        >
          <span className="material-symbols-outlined text-primary text-2xl">
            support_agent
          </span>
          <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Поддержка
          </span>
        </button>
      </div>

      {/* Withdrawal Modal */}
      {user && (
        <WithdrawalModal
          isOpen={isWithdrawalModalOpen}
          onClose={() => setIsWithdrawalModalOpen(false)}
          balance={totalBalance}
          hasPendingWithdrawal={!!pendingWithdrawal}
          onSuccess={handleWithdrawalSuccess}
        />
      )}
    </div>
  );
}
