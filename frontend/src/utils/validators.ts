/**
 * Проверяет корректность номера телефона в российском формате
 * @param phone - номер телефона (может содержать форматирование)
 * @returns true если номер корректен
 */
export function validatePhone(phone: string): boolean {
  // Убираем всё кроме цифр
  const digits = phone.replace(/\D/g, '');

  // Проверяем что начинается с 7 или 8 и всего 11 цифр
  return (digits.startsWith('7') || digits.startsWith('8')) && digits.length === 11;
}

/**
 * Проверяет корректность номера карты
 * @param cardNumber - номер карты (может содержать пробелы)
 * @returns true если номер корректен (16 цифр)
 */
export function validateCardNumber(cardNumber: string): boolean {
  // Убираем всё кроме цифр
  const digits = cardNumber.replace(/\D/g, '');

  // Проверяем что ровно 16 цифр
  return digits.length === 16;
}

/**
 * Валидирует сумму для вывода средств
 * @param amount - сумма для вывода
 * @param balance - текущий баланс пользователя
 * @param minWithdrawal - минимальная сумма вывода из конфига
 * @returns сообщение об ошибке или null если всё ок
 */
export function validateAmount(
  amount: number,
  balance: number,
  minWithdrawal: number
): string | null {
  if (!amount || amount <= 0) {
    return 'Введите сумму';
  }

  if (amount < minWithdrawal) {
    return `Минимальная сумма вывода: ${minWithdrawal} ₽`;
  }

  if (amount > balance) {
    return 'Недостаточно средств';
  }

  return null;
}
