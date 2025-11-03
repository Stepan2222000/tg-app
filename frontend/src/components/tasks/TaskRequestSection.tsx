import { TaskLimitIndicator } from './TaskLimitIndicator';
import { formatCurrency } from '../../utils/formatters';
import type { TaskType } from '../../types';

interface TaskRequestSectionProps {
  activeTaskCount: number;
  maxActiveTasks: number;
  simpleTaskPrice: number;
  phoneTaskPrice: number;
  onRequestTask: (type: TaskType) => void;
  isLoading: boolean;
}

export function TaskRequestSection({
  activeTaskCount,
  maxActiveTasks,
  simpleTaskPrice,
  phoneTaskPrice,
  onRequestTask,
  isLoading,
}: TaskRequestSectionProps) {
  const canRequestTask = activeTaskCount < maxActiveTasks;

  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-black text-gray-900 dark:text-gray-100 mb-4 text-center">
        Получить новую задачу
      </h2>

      {/* Task Limit Indicator */}
      <div className="flex justify-center mb-6">
        <TaskLimitIndicator current={activeTaskCount} max={maxActiveTasks} />
      </div>

      {/* Limit Reached Message */}
      {!canRequestTask && (
        <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
          <p className="text-center text-sm text-amber-800 dark:text-amber-200 font-medium">
            Достигнут лимит активных задач. Завершите текущие задачи, чтобы взять новые.
          </p>
        </div>
      )}

      {/* Task Type Buttons */}
      <div className="space-y-3 mb-4">
        {/* Simple Task Button */}
        <button
          onClick={() => onRequestTask('simple')}
          disabled={!canRequestTask || isLoading}
          className={`w-full py-4 px-6 rounded-xl font-bold text-lg transition-all ${
            canRequestTask && !isLoading
              ? 'bg-primary text-white hover:bg-[#c59563]'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-500 cursor-not-allowed'
          }`}
        >
          Обычная задача - {formatCurrency(simpleTaskPrice)}
        </button>
        <p className="text-xs text-text-muted dark:text-text-muted-dark text-center px-4">
          Отправить сообщение продавцу и дождаться прочтения
        </p>

        {/* Phone Task Button */}
        <button
          onClick={() => onRequestTask('phone')}
          disabled={!canRequestTask || isLoading}
          className={`w-full py-4 px-6 rounded-xl font-bold text-lg transition-all ${
            canRequestTask && !isLoading
              ? 'bg-primary text-white hover:bg-[#c59563]'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-500 cursor-not-allowed'
          }`}
        >
          Задача с номером - {formatCurrency(phoneTaskPrice)}
        </button>
        <p className="text-xs text-text-muted dark:text-text-muted-dark text-center px-4">
          Получить номер телефона продавца в переписке
        </p>
      </div>
    </div>
  );
}
