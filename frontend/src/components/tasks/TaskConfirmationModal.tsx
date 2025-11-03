import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { formatCurrency } from '../../utils/formatters';
import type { TaskType } from '../../types';

interface TaskConfirmationModalProps {
  isOpen: boolean;
  taskType: TaskType;
  price: number;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

export function TaskConfirmationModal({
  isOpen,
  taskType,
  price,
  onConfirm,
  onCancel,
  isLoading,
}: TaskConfirmationModalProps) {
  const taskTypeLabel = taskType === 'phone' ? 'Задача с номером' : 'Обычная задача';
  const taskDescription =
    taskType === 'phone'
      ? 'Получить номер телефона продавца в переписке'
      : 'Отправить сообщение продавцу и дождаться прочтения';

  return (
    <Modal isOpen={isOpen} onClose={onCancel} title="Подтверждение задачи">
      <div className="space-y-6">
        {/* Info Icon */}
        <div className="flex justify-center">
          <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-5xl">help</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-center text-text-muted dark:text-text-muted-dark">
          Вы собираетесь взять новую задачу. После подтверждения у вас будет 24 часа на её
          выполнение.
        </p>

        {/* Task Details */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted dark:text-text-muted-dark">
              Тип задачи:
            </span>
            <span className="text-base font-semibold text-gray-900 dark:text-gray-100">
              {taskTypeLabel}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted dark:text-text-muted-dark">
              Вознаграждение:
            </span>
            <span className="text-base font-semibold text-gray-900 dark:text-gray-100">
              {formatCurrency(price)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted dark:text-text-muted-dark">
              Время на выполнение:
            </span>
            <span className="text-base font-semibold text-gray-900 dark:text-gray-100">
              24 часа
            </span>
          </div>
        </div>

        {/* Task Description */}
        <p className="text-sm text-text-muted dark:text-text-muted-dark text-center italic">
          {taskDescription}
        </p>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            variant="secondary"
            fullWidth
            onClick={onCancel}
            disabled={isLoading}
          >
            Отмена
          </Button>
          <Button
            variant="primary"
            fullWidth
            onClick={onConfirm}
            loading={isLoading}
            disabled={isLoading}
          >
            Взять задачу
          </Button>
        </div>
      </div>
    </Modal>
  );
}
