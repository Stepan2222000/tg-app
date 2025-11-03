import { useNotification } from '../../hooks/useNotification';
import { copyToClipboard } from '../../utils/taskHelpers';

interface TaskInstructionsCardProps {
  instructions: string;
  avitoUrl: string;
}

export function TaskInstructionsCard({ instructions, avitoUrl }: TaskInstructionsCardProps) {
  const { showSuccess, showError } = useNotification();

  const handleCopyLink = async () => {
    const success = await copyToClipboard(avitoUrl);
    if (success) {
      showSuccess('Ссылка скопирована');
    } else {
      showError('Не удалось скопировать ссылку');
    }
  };

  // Parse instructions into numbered list
  const instructionsList = instructions
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Инструкция</h2>

      {/* Instructions List */}
      <ol className="list-decimal list-inside space-y-2 mb-4 text-text-muted dark:text-text-muted-dark">
        {instructionsList.map((instruction, index) => (
          <li key={index} className="leading-relaxed">
            {instruction.replace(/^\d+\.\s*/, '')}
          </li>
        ))}
      </ol>

      {/* Copy Avito Link Button */}
      <button
        onClick={handleCopyLink}
        className="w-full bg-primary text-white py-3 px-4 rounded-xl font-semibold hover:bg-[#c59563] transition-colors"
      >
        Скопировать ссылку на объявление Avito
      </button>
    </div>
  );
}
