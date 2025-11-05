import { useState, useRef, useEffect } from 'react';

interface SelectOption {
  value: string;
  label: string;
  icon?: string;
}

interface SelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
}

export function Select({
  options,
  value,
  onChange,
  placeholder = 'Выберите',
  label,
  error,
  disabled = false,
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  // Закрываем dropdown при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const baseStyles =
    'w-full px-4 py-3 rounded-xl border transition-all duration-200 font-display cursor-pointer';

  const normalStyles =
    'border-gray-300 dark:border-gray-600 bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100 hover:border-primary hover:shadow-md';

  const errorStyles =
    'border-red-500 dark:border-red-500 bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100';

  const disabledStyles = 'bg-gray-100 dark:bg-gray-800 cursor-not-allowed opacity-60';

  const selectStyles = `${baseStyles} ${error ? errorStyles : normalStyles} ${
    disabled ? disabledStyles : ''
  }`;

  return (
    <div className="w-full" ref={selectRef}>
      {label && (
        <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark mb-2">
          {label}
        </label>
      )}

      <div className="relative">
        {/* Select Button */}
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          className={selectStyles}
          disabled={disabled}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {selectedOption?.icon && (
                <span className="text-2xl">{selectedOption.icon}</span>
              )}
              <span className={selectedOption ? '' : 'text-gray-400 dark:text-gray-500'}>
                {selectedOption?.label || placeholder}
              </span>
            </div>
            <span
              className={`material-symbols-outlined text-gray-400 transition-transform duration-200 ${
                isOpen ? 'rotate-180' : ''
              }`}
            >
              expand_more
            </span>
          </div>
        </button>

        {/* Dropdown Menu */}
        {isOpen && !disabled && (
          <div className="absolute z-50 w-full mt-2 py-2 bg-white dark:bg-card-dark border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl animate-slide-down">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => handleSelect(option.value)}
                className={`w-full px-4 py-3 text-left flex items-center gap-3 transition-all duration-150 ${
                  option.value === value
                    ? 'bg-primary/10 text-primary dark:bg-primary/20'
                    : 'text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                {option.icon && <span className="text-2xl">{option.icon}</span>}
                <span className="font-medium">{option.label}</span>
                {option.value === value && (
                  <span className="material-symbols-outlined ml-auto text-primary">
                    check
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
}
