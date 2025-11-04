import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { formatCurrency } from '../utils/formatters';
import { copyToClipboard } from '../utils/clipboard';
import { mockReferralStats } from '../mocks/referralMocks';
import { ReferralHelpModal } from '../components/ReferralHelpModal';
import type { ReferralStats } from '../types';

export function ReferralsPage() {
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();

  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);

  // Get bot username from env
  const botUsername = import.meta.env.VITE_BOT_USERNAME || 'avito_tasker_bot';
  const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

  // Load referral stats
  useEffect(() => {
    let isMounted = true;

    const loadStats = async () => {
      try {
        if (useMockData) {
          // Use mock data from file
          if (isMounted) {
            setStats(mockReferralStats);
            setIsLoading(false);
          }
          return;
        }

        const data = await apiService.getReferralStats();

        if (isMounted) {
          setStats(data);
        }
      } catch (error) {
        console.error('Failed to load referral stats:', error);
        if (isMounted) {
          showError(
            error instanceof Error
              ? error.message
              : 'Не удалось загрузить статистику'
          );
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadStats();

    return () => {
      isMounted = false;
    };
  }, [showError, useMockData]);

  // Copy referral link to clipboard
  const handleCopyLink = async () => {
    if (!stats) return;

    try {
      let link: string;

      if (useMockData) {
        // Mock link for visualization
        link = `https://t.me/${botUsername}?start=ref_123456789`;
      } else {
        const response = await apiService.getReferralLink();
        link = response.link;
      }

      await copyToClipboard(link);
      showSuccess('Ссылка скопирована');
    } catch (error) {
      console.error('Failed to copy link:', error);
      showError('Не удалось скопировать ссылку');
    }
  };

  // Handle back button
  const handleBack = () => {
    navigate('/');
  };

  if (isLoading) {
    return (
      <div
        className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center"
        role="status"
        aria-label="Загрузка данных"
      >
        <span className="material-symbols-outlined text-5xl text-primary animate-spin">
          progress_activity
        </span>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const hasReferrals = stats.referrals.length > 0;

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark font-display">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background-light/80 dark:bg-background-dark/80 p-4 backdrop-blur-sm">
        <div className="flex size-12 shrink-0 items-center justify-start">
          <button
            onClick={handleBack}
            aria-label="Вернуться на главную страницу"
            className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full text-text-primary-light dark:text-text-primary-dark hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <span className="material-symbols-outlined" aria-hidden="true">
              arrow_back
            </span>
          </button>
        </div>
        <h1 className="flex-1 text-center text-lg font-bold leading-tight tracking-[-0.015em] text-text-primary-light dark:text-text-primary-dark">
          Реферальная программа
        </h1>
        <div className="flex w-12 items-center justify-end">
          <button
            onClick={() => setIsHelpModalOpen(true)}
            aria-label="Показать справку о реферальной программе"
            className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full text-text-primary-light dark:text-text-primary-dark hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <span className="material-symbols-outlined" aria-hidden="true">
              help
            </span>
          </button>
        </div>
      </div>

      {/* Content */}
      <main className="flex flex-1 flex-col items-center px-4 pb-8">
        {/* Referral Link Card */}
        <div className="flex w-full max-w-md flex-col items-center justify-start rounded-xl bg-card-light dark:bg-card-dark p-6 text-center shadow-md">
          <p className="text-base font-medium text-text-primary-light dark:text-text-primary-dark">
            Ваша уникальная ссылка
          </p>
          <p className="mt-2 text-sm text-text-secondary-light dark:text-text-secondary-dark break-all">
            https://t.me/{botUsername}?start=ref_...
          </p>
          <button
            onClick={handleCopyLink}
            aria-label="Скопировать реферальную ссылку"
            className="mt-4 flex min-w-[120px] max-w-[480px] w-full cursor-pointer items-center justify-center gap-2 overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-medium leading-normal hover:bg-primary/90 transition-colors"
          >
            <span className="material-symbols-outlined text-base" aria-hidden="true">
              content_copy
            </span>
            <span className="truncate">Копировать</span>
          </button>
        </div>

        {/* Statistics Cards */}
        <div className="mt-4 grid w-full max-w-md grid-cols-2 gap-4">
          {/* Total Referrals */}
          <div className="flex flex-col items-center gap-1 rounded-xl bg-card-light dark:bg-card-dark p-4 text-center shadow-md">
            <p className="text-sm font-medium text-text-secondary-light dark:text-text-secondary-dark">
              Приглашено друзей
            </p>
            <p className="text-2xl font-bold leading-tight tracking-tight text-text-primary-light dark:text-text-primary-dark">
              {stats.total_referrals}
            </p>
          </div>

          {/* Total Earnings */}
          <div className="flex flex-col items-center gap-1 rounded-xl bg-card-light dark:bg-card-dark p-4 text-center shadow-md">
            <p className="text-sm font-medium text-text-secondary-light dark:text-text-secondary-dark">
              Ваш заработок
            </p>
            <p className="text-2xl font-bold leading-tight tracking-tight text-primary">
              {formatCurrency(stats.total_earnings)}
            </p>
          </div>
        </div>

        {/* Referrals List or Empty State */}
        <div className="w-full max-w-md mt-8">
          <h2 className="text-text-primary-light dark:text-text-primary-dark text-xl font-bold leading-tight tracking-[-0.015em] pb-3 text-center">
            Ваши рефералы
          </h2>

          {hasReferrals ? (
            <div className="flex flex-col gap-3 pb-8" role="list">
              {stats.referrals.map((referral) => (
                <div
                  key={referral.telegram_id}
                  role="listitem"
                  className="flex items-center gap-4 rounded-xl bg-card-light dark:bg-card-dark p-4 shadow-md"
                >
                  <div className="flex-1">
                    <p className="text-text-primary-light dark:text-text-primary-dark text-base font-medium leading-normal">
                      {referral.username
                        ? `@${referral.username}`
                        : `ID ${referral.telegram_id}`}
                    </p>
                    <p className="text-text-secondary-light dark:text-text-secondary-dark text-sm font-normal leading-normal">
                      Обычные: {referral.simple_tasks}, С номером:{' '}
                      {referral.phone_tasks}
                    </p>
                  </div>
                  <div className="shrink-0">
                    <p className="text-primary text-base font-medium leading-normal">
                      + {formatCurrency(referral.earnings)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div
              className="flex flex-col items-center justify-center rounded-lg bg-card-light dark:bg-card-dark p-8 text-center shadow-md"
              role="status"
            >
              <span className="material-symbols-outlined text-5xl text-primary" aria-hidden="true">
                group_add
              </span>
              <h3 className="mt-4 text-lg font-bold text-text-primary-light dark:text-text-primary-dark">
                Пока нет рефералов
              </h3>
              <p className="mt-1 text-sm text-text-secondary-light dark:text-text-secondary-dark">
                Поделитесь ссылкой с друзьями и начните зарабатывать вместе!
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Help Modal */}
      <ReferralHelpModal
        isOpen={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
        commission={0.5}
      />
    </div>
  );
}
