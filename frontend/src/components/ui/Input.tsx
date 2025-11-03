import React from 'react';
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
}: InputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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

  const baseStyles =
    'w-full px-4 py-3 rounded-xl border transition-all duration-200 font-display';

  const normalStyles =
    'border-gray-300 dark:border-gray-600 bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent';

  const errorStyles =
    'border-red-500 dark:border-red-500 bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent';

  const disabledStyles = 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed opacity-60';

  const inputStyles = `${baseStyles} ${error ? errorStyles : normalStyles} ${
    disabled ? disabledStyles : ''
  }`;

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark mb-2">
          {label}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        className={inputStyles}
      />
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}
