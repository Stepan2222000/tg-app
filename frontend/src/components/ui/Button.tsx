import type { ReactNode } from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  onClick?: () => void;
  children: ReactNode;
  type?: 'button' | 'submit' | 'reset';
}

export function Button({
  variant = 'primary',
  disabled = false,
  loading = false,
  fullWidth = false,
  onClick,
  children,
  type = 'button',
}: ButtonProps) {
  const baseStyles =
    'px-6 py-3.5 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2 shadow-md hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]';

  const variantStyles = {
    primary:
      'bg-gradient-to-r from-primary to-[#c59563] text-white hover:from-[#c59563] hover:to-primary disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-md',
    secondary:
      'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 active:bg-gray-400 dark:active:bg-gray-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed disabled:transform-none',
  };

  const widthStyles = fullWidth ? 'w-full' : '';

  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      className={`${baseStyles} ${variantStyles[variant]} ${widthStyles}`}
      onClick={onClick}
      disabled={isDisabled}
    >
      {loading && (
        <span className="material-symbols-outlined animate-spin text-xl">
          progress_activity
        </span>
      )}
      {children}
    </button>
  );
}
