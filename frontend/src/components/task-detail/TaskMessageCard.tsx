import { useNotification } from '../../hooks/useNotification';
import { copyToClipboard } from '../../utils/taskHelpers';

interface TaskMessageCardProps {
  messageText: string;
}

export function TaskMessageCard({ messageText }: TaskMessageCardProps) {
  const { showSuccess, showError } = useNotification();

  const handleCopyText = async () => {
    const success = await copyToClipboard(messageText);
    if (success) {
      showSuccess('Текст скопирован');
    } else {
      showError('Не удалось скопировать текст');
    }
  };

  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
        Текст для отправки продавцу
      </h2>

      {/* Message Text */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-4 relative">
        <p className="text-text-muted dark:text-text-muted-dark leading-relaxed pr-10">
          {messageText}
        </p>
        <button
          onClick={handleCopyText}
          className="absolute top-3 right-3 p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
          aria-label="Копировать текст"
        >
          <span className="material-symbols-outlined text-gray-600 dark:text-gray-400 text-xl">
            content_copy
          </span>
        </button>
      </div>

      <p className="text-xs text-text-muted dark:text-text-muted-dark">
        Нажмите на иконку копирования, чтобы скопировать текст в буфер обмена
      </p>
    </div>
  );
}
