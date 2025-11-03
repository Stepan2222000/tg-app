import { useCountdown } from '../../hooks/useCountdown';
import { formatDate, formatTimer } from '../../utils/formatters';
import type { TaskType } from '../../types';

interface TaskTimerCardProps {
  taskType: TaskType;
  deadline: string;
  assignedAt: string;
}

export function TaskTimerCard({ taskType, deadline, assignedAt }: TaskTimerCardProps) {
  const { hours, minutes, seconds, isExpired } = useCountdown(deadline, assignedAt);

  const taskTypeLabel =
    taskType === 'phone' ? 'Задача с номером' : 'Обычная задача';
  const taskTypeColor = taskType === 'phone' ? 'text-primary' : 'text-primary';

  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
      {/* Task Type */}
      <p className={`text-center text-sm font-medium ${taskTypeColor} mb-2`}>
        Тип: {taskTypeLabel}
      </p>

      {/* Timer */}
      <div className="text-center mb-3">
        <p className="text-text-muted dark:text-text-muted-dark text-sm mb-1">
          {isExpired ? 'Время истекло' : 'Осталось времени'}
        </p>
        <p
          className={`text-6xl font-black ${
            isExpired
              ? 'text-red-600 dark:text-red-500'
              : 'text-gray-900 dark:text-gray-100'
          }`}
        >
          {formatTimer(hours, minutes, seconds)}
        </p>
      </div>

      {/* Deadline */}
      <p className="text-center text-sm text-text-muted dark:text-text-muted-dark">
        Дедлайн: {formatDate(deadline)}
      </p>
    </div>
  );
}
