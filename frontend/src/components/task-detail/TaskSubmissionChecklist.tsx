interface TaskSubmissionChecklistProps {
  requirements: string[];
}

export function TaskSubmissionChecklist({ requirements }: TaskSubmissionChecklistProps) {
  if (requirements.length === 0) {
    return null;
  }

  return (
    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
      <div className="flex items-start gap-2">
        <span className="material-symbols-outlined text-amber-600 dark:text-amber-400 text-xl flex-shrink-0 mt-0.5">
          info
        </span>
        <div className="flex-1">
          <p className="text-sm font-medium text-amber-900 dark:text-amber-200 mb-2">
            Для отправки необходимо:
          </p>
          <ul className="space-y-1">
            {requirements.map((requirement, index) => (
              <li
                key={index}
                className="text-sm text-amber-800 dark:text-amber-300 flex items-center gap-2"
              >
                <span className="w-1 h-1 bg-amber-600 dark:bg-amber-400 rounded-full flex-shrink-0" />
                {requirement}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
