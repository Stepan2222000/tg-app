import { ActiveTaskCard } from './ActiveTaskCard';
import type { TaskAssignment } from '../../types';

interface ActiveTasksListProps {
  tasks: TaskAssignment[];
  onTaskClick: (assignmentId: number) => void;
}

export function ActiveTasksList({ tasks, onTaskClick }: ActiveTasksListProps) {
  if (tasks.length === 0) {
    return (
      <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-8 text-center">
        <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
          <span className="material-symbols-outlined text-4xl text-gray-400">
            inbox
          </span>
        </div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Нет активных задач
        </h3>
        <p className="text-text-muted dark:text-text-muted-dark">
          Возьмите задачу выше, чтобы начать зарабатывать
        </p>
      </div>
    );
  }

  // Sort tasks by deadline (most urgent first)
  const sortedTasks = [...tasks].sort((a, b) => {
    return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
  });

  return (
    <div className="space-y-3">
      {sortedTasks.map((task) => (
        <ActiveTaskCard
          key={task.id}
          assignment={task}
          onClick={() => onTaskClick(task.id)}
        />
      ))}
    </div>
  );
}
