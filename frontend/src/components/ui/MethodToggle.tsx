import type { WithdrawalMethod } from '../../types';

interface MethodToggleProps {
  method: WithdrawalMethod;
  onChange: (method: WithdrawalMethod) => void;
  disabled?: boolean;
}

const methodConfig = {
  card: {
    label: 'Банковская карта',
    icon: '💳',
    gradient: 'from-blue-500 to-blue-600',
  },
  sbp: {
    label: 'СБП',
    icon: '⚡',
    gradient: 'from-purple-500 to-purple-600',
  },
};

export function MethodToggle({ method, onChange, disabled = false }: MethodToggleProps) {
  return (
    <div className="grid grid-cols-2 gap-3 p-1.5 bg-gray-100 dark:bg-gray-800 rounded-2xl">
      {(Object.entries(methodConfig) as [WithdrawalMethod, typeof methodConfig.card][]).map(
        ([key, config]) => {
          const isActive = method === key;

          return (
            <button
              key={key}
              type="button"
              onClick={() => !disabled && onChange(key)}
              disabled={disabled}
              className={`
                relative overflow-hidden py-3.5 px-4 rounded-xl font-semibold
                transition-all duration-300 ease-out
                flex items-center justify-center gap-2.5
                ${
                  isActive
                    ? 'bg-gradient-to-br ' +
                      config.gradient +
                      ' text-white shadow-lg transform scale-[1.02]'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-650 hover:scale-[1.01]'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {/* Icon with animation */}
              <span
                className={`text-2xl transition-transform duration-300 ${
                  isActive ? 'scale-110' : 'scale-100'
                }`}
              >
                {config.icon}
              </span>

              {/* Label */}
              <span className="text-sm">{config.label}</span>

              {/* Active indicator with glow effect */}
              {isActive && (
                <div className="absolute inset-0 bg-white opacity-20 animate-pulse rounded-xl" />
              )}
            </button>
          );
        }
      )}
    </div>
  );
}
