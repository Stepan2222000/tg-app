import { useCountdown } from '../../hooks/useCountdown';
import { formatCountdown } from '../../utils/formatters';
import { generateDisplayId, getTimerColorClasses } from '../../utils/taskHelpers';
import type { TaskAssignment } from '../../types';

interface ActiveTaskCardProps {
  assignment: TaskAssignment;
  onClick: () => void;
}

export function ActiveTaskCard({ assignment, onClick }: ActiveTaskCardProps) {
  const { hours, minutes, percentage } = useCountdown(
    assignment.deadline,
    assignment.assigned_at
  );

  const taskType = assignment.task?.type || 'simple';
  const displayId = generateDisplayId(assignment.id);
  const colorClasses = getTimerColorClasses(percentage);

  // Icons based on task type
  const taskIcon = taskType === 'phone' ? 'pin' : 'task_alt';
  const taskTypeLabel = taskType === 'phone' ? 'Задача с номером' : 'Обычная задача';

  return (
    <button
      onClick={onClick}
      className="w-full bg-card-light dark:bg-card-dark rounded-xl shadow-md p-4 flex items-center gap-4 hover:shadow-lg transition-all"
    >
      {/* Icon */}
      <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-primary text-3xl">{taskIcon}</span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Task ID and Timer */}
        <div className="flex items-center justify-between gap-2 mb-1">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
            Задача {displayId}
          </h3>
          <span className={`text-lg font-bold ${colorClasses.text} flex-shrink-0`}>
            {formatCountdown(hours, minutes)}
          </span>
        </div>

        {/* Task Type */}
        <p className="text-sm text-text-muted dark:text-text-muted-dark mb-3 text-left">
          {taskTypeLabel}
        </p>

        {/* Progress Bar */}
        <div className={`w-full h-1.5 rounded-full ${colorClasses.progressBg} overflow-hidden`}>
          <div
            className={`h-full ${colorClasses.bg} transition-all duration-300`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Chevron */}
      <span className="material-symbols-outlined text-gray-400 text-3xl flex-shrink-0">
        chevron_right
      </span>
    </button>
  );
}
