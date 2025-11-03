import { useState, useEffect } from 'react';

export interface CountdownResult {
  hours: number;
  minutes: number;
  seconds: number;
  percentage: number; // 0-100, процент оставшегося времени
  isExpired: boolean;
}

/**
 * Хук для обратного отсчёта времени до deadline
 * @param deadline - ISO строка даты окончания (например, "2024-12-25T23:59:00Z")
 * @param assignedAt - ISO строка даты начала (опционально, по умолчанию deadline - 24 часа)
 * @returns объект с оставшимся временем и процентом
 */
export function useCountdown(deadline: string, assignedAt?: string): CountdownResult {
  const [timeLeft, setTimeLeft] = useState<CountdownResult>({
    hours: 0,
    minutes: 0,
    seconds: 0,
    percentage: 0,
    isExpired: false,
  });

  useEffect(() => {
    const deadlineDate = new Date(deadline);

    // Динамически вычисляем totalDuration
    const startDate = assignedAt
      ? new Date(assignedAt)
      : new Date(deadlineDate.getTime() - 24 * 60 * 60 * 1000); // По умолчанию 24 часа назад

    const totalDuration = deadlineDate.getTime() - startDate.getTime();

    const updateCountdown = () => {
      const now = new Date();
      const diff = deadlineDate.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeLeft({
          hours: 0,
          minutes: 0,
          seconds: 0,
          percentage: 0,
          isExpired: true,
        });
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);
      const percentage = Math.round((diff / totalDuration) * 100);

      setTimeLeft({
        hours,
        minutes,
        seconds,
        percentage: Math.min(Math.max(percentage, 0), 100), // Ограничиваем 0-100
        isExpired: false,
      });
    };

    // Сразу обновляем при монтировании
    updateCountdown();

    // Обновляем каждую секунду
    const interval = setInterval(updateCountdown, 1000);

    // Очищаем интервал при размонтировании
    return () => clearInterval(interval);
  }, [deadline, assignedAt]);

  return timeLeft;
}
