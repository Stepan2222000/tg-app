import { useState, type ChangeEvent } from 'react';
import { formatPhone, formatCardNumber } from '../../utils/formatters';

interface InputProps {
  type?: 'text' | 'number' | 'tel';
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  mask?: 'phone' | 'card' | 'none';
  disabled?: boolean;
  icon?: string;
}

export function Input({
  type = 'text',
  value,
  onChange,
  placeholder,
  label,
  error,
  mask = 'none',
  disabled = false,
  icon,
}: InputProps) {
  const [isFocused, setIsFocused] = useState(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    let newValue = e.target.value;

    // Применяем маску
    if (mask === 'phone') {
      newValue = formatPhone(newValue);
    } else if (mask === 'card') {
      newValue = formatCardNumber(newValue);
      // Ограничиваем 19 символов (16 цифр + 3 пробела)
      if (newValue.length > 19) {
        newValue = newValue.slice(0, 19);
      }
    }

    onChange(newValue);
  };

  // Auto-detect icon based on mask
  const displayIcon = icon || (mask === 'phone' ? '📱' : mask === 'card' ? '💳' : null);

  const baseStyles =
    'w-full py-3 rounded-xl border transition-all duration-200 font-display';

  const normalStyles =
    'border-gray-300 dark:border-gray-600 bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary hover:border-gray-400 dark:hover:border-gray-500';

  const errorStyles =
    'border-red-500 dark:border-red-500 bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500';

  const disabledStyles = 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed opacity-60';

  const inputStyles = `${baseStyles} ${error ? errorStyles : normalStyles} ${
    disabled ? disabledStyles : ''
  } ${displayIcon ? 'pl-12 pr-4' : 'px-4'}`;

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {displayIcon && (
          <div
            className={`absolute left-4 top-1/2 -translate-y-1/2 text-2xl transition-transform duration-200 ${
              isFocused ? 'scale-110' : 'scale-100'
            }`}
          >
            {displayIcon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          className={inputStyles}
        />
        {/* Subtle glow effect on focus */}
        {isFocused && !error && !disabled && (
          <div className="absolute inset-0 rounded-xl bg-primary opacity-5 pointer-events-none" />
        )}
      </div>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}
