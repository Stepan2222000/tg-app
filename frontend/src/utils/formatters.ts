/**
 * Форматирует сумму в рубли с разделителями тысяч
 * @param amount - сумма в числовом формате
 * @returns строка вида "1 000 ₽"
 */
export function formatCurrency(amount: number): string {
  return `${amount.toLocaleString('ru-RU')} ₽`;
}

/**
 * Форматирует дату в русский формат
 * @param dateString - ISO string дата
 * @returns строка вида "25.12.2024 в 23:59" или "Invalid Date" если дата невалидна
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);

  // Проверяем валидность даты
  if (isNaN(date.getTime())) {
    return 'Invalid Date';
  }

  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${day}.${month}.${year} в ${hours}:${minutes}`;
}

/**
 * Форматирует номер телефона в российский формат
 * @param phone - строка с цифрами телефона
 * @returns строка вида "+7 (999) 999-99-99"
 */
export function formatPhone(phone: string): string {
  // Убираем все нецифровые символы
  const digits = phone.replace(/\D/g, '');

  // Если начинается с 8, заменяем на 7
  const normalized = digits.startsWith('8') ? '7' + digits.slice(1) : digits;

  // Форматируем
  if (normalized.length >= 11) {
    return `+7 (${normalized.slice(1, 4)}) ${normalized.slice(4, 7)}-${normalized.slice(7, 9)}-${normalized.slice(9, 11)}`;
  }

  return phone;
}

/**
 * Форматирует номер карты с пробелами
 * @param cardNumber - строка с цифрами карты
 * @returns строка вида "0000 0000 0000 0000"
 */
export function formatCardNumber(cardNumber: string): string {
  // Убираем все нецифровые символы
  const digits = cardNumber.replace(/\D/g, '');

  // Разбиваем по 4 цифры
  const formatted = digits.match(/.{1,4}/g)?.join(' ') || digits;

  return formatted;
}

/**
 * Форматирует время обратного отсчёта для карточек задач
 * @param hours - количество часов
 * @param minutes - количество минут
 * @returns строка вида "23ч 15м"
 */
export function formatCountdown(hours: number, minutes: number): string {
  return `${hours}ч ${minutes}м`;
}

/**
 * Форматирует время как таймер (для детальной страницы задачи)
 * @param hours - количество часов
 * @param minutes - количество минут
 * @param seconds - количество секунд
 * @returns строка вида "01:23:45"
 */
export function formatTimer(hours: number, minutes: number, seconds: number): string {
  const h = String(hours).padStart(2, '0');
  const m = String(minutes).padStart(2, '0');
  const s = String(seconds).padStart(2, '0');

  return `${h}:${m}:${s}`;
}
