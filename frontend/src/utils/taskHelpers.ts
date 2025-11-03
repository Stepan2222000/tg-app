/**
 * Генерирует отображаемый ID задачи в формате #A8B12
 * @param id - числовой ID задачи
 * @returns строка вида "#A8B12"
 */
export function generateDisplayId(id: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const hash = id.toString().split('').reduce((acc, char) => {
    return acc + char.charCodeAt(0);
  }, 0);

  let result = '#';
  for (let i = 0; i < 5; i++) {
    const index = (hash + i * 7) % chars.length;
    result += chars[index];
  }

  return result;
}

/**
 * Возвращает цвет таймера на основе процента оставшегося времени
 * @param percentage - процент оставшегося времени (0-100)
 * @returns 'green' | 'amber' | 'red'
 */
export function getTimerColor(percentage: number): 'green' | 'amber' | 'red' {
  if (percentage > 83) return 'green'; // > 20 часов
  if (percentage > 33) return 'amber'; // 8-20 часов
  return 'red'; // < 8 часов
}

/**
 * Копирует текст в буфер обмена
 * @param text - текст для копирования
 * @returns Promise<boolean> - true если успешно
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    // Современный способ
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    // Fallback для старых браузеров
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);

    return successful;
  } catch (error) {
    console.error('Failed to copy text:', error);
    return false;
  }
}

/**
 * Получает Tailwind CSS классы для цвета таймера
 * @param percentage - процент оставшегося времени
 * @returns объект с классами для текста и фона
 */
export function getTimerColorClasses(percentage: number) {
  const color = getTimerColor(percentage);

  const colorClasses = {
    green: {
      text: 'text-green-600 dark:text-green-500',
      bg: 'bg-green-500',
      progressBg: 'bg-green-100 dark:bg-green-900/30',
    },
    amber: {
      text: 'text-amber-600 dark:text-amber-500',
      bg: 'bg-amber-500',
      progressBg: 'bg-amber-100 dark:bg-amber-900/30',
    },
    red: {
      text: 'text-red-600 dark:text-red-500',
      bg: 'bg-red-500',
      progressBg: 'bg-red-100 dark:bg-red-900/30',
    },
  };

  return colorClasses[color];
}
