interface TaskLimitIndicatorProps {
  current: number;
  max: number;
}

export function TaskLimitIndicator({ current, max }: TaskLimitIndicatorProps) {
  const percentage = (current / max) * 100;
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg className="w-24 h-24 transform -rotate-90">
        {/* Background circle */}
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="text-primary transition-all duration-300"
        />
      </svg>
      {/* Text in center */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-black text-gray-900 dark:text-gray-100">
          {current}/{max}
        </span>
      </div>
    </div>
  );
}
