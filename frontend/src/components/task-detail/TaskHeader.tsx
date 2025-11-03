interface TaskHeaderProps {
  taskId: string;
  onBack: () => void;
}

export function TaskHeader({ taskId, onBack }: TaskHeaderProps) {
  return (
    <header className="sticky top-0 z-30 bg-background-light dark:bg-background-dark border-b border-gray-200 dark:border-gray-700 px-4 py-3">
      <div className="max-w-2xl mx-auto flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <span className="material-symbols-outlined text-2xl text-gray-600 dark:text-gray-400">
            arrow_back
          </span>
        </button>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Задача {taskId}</h1>
      </div>
    </header>
  );
}
