import { useState, useEffect } from 'react';
import { Modal } from './ui/Modal';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { apiService } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { formatCurrency } from '../utils/formatters';
import { validateAmount, validateCardNumber, validatePhone } from '../utils/validators';
import type { WithdrawalMethod } from '../types';

interface WithdrawalModalProps {
  isOpen: boolean;
  onClose: () => void;
  balance: number;
  hasPendingWithdrawal: boolean;
  onSuccess: () => void;
}

const BANKS = [
  'Сбербанк',
  'Тинькофф',
  'Альфа-Банк',
  'ВТБ',
  'Райффайзен',
  'Открытие',
];

export function WithdrawalModal({
  isOpen,
  onClose,
  balance,
  hasPendingWithdrawal,
  onSuccess,
}: WithdrawalModalProps) {
  const { showSuccess, showError } = useNotification();
  const [method, setMethod] = useState<WithdrawalMethod>('card');
  const [amount, setAmount] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [cardholderName, setCardholderName] = useState('');
  const [bankName, setBankName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [minWithdrawal, setMinWithdrawal] = useState(100);

  // Загружаем конфиг при монтировании
  useEffect(() => {
    let isMounted = true;

    const loadConfig = async () => {
      try {
        const config = await apiService.getConfig();
        // Устанавливаем state только если компонент еще смонтирован
        if (isMounted) {
          setMinWithdrawal(config.min_withdrawal);
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    };

    loadConfig();

    // Cleanup: отмечаем что компонент размонтирован
    return () => {
      isMounted = false;
    };
  }, []);

  // Сбрасываем форму при открытии
  useEffect(() => {
    if (isOpen) {
      setAmount('');
      setCardNumber('');
      setCardholderName('');
      setBankName('');
      setPhoneNumber('');
      setErrors({});
    }
  }, [isOpen]);

  const handleWithdrawAll = () => {
    setAmount(balance.toString());
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Валидация суммы
    const amountError = validateAmount(Number(amount), balance, minWithdrawal);
    if (amountError) {
      newErrors.amount = amountError;
    }

    // Валидация в зависимости от метода
    if (method === 'card') {
      if (!cardNumber.trim()) {
        newErrors.cardNumber = 'Введите номер карты';
      } else if (!validateCardNumber(cardNumber)) {
        newErrors.cardNumber = 'Номер карты должен содержать 16 цифр';
      }

      if (!cardholderName.trim()) {
        newErrors.cardholderName = 'Введите ФИО получателя';
      }
    } else {
      // СБП
      if (!bankName) {
        newErrors.bankName = 'Выберите банк';
      }

      if (!phoneNumber.trim()) {
        newErrors.phoneNumber = 'Введите номер телефона';
      } else if (!validatePhone(phoneNumber)) {
        newErrors.phoneNumber = 'Введите корректный номер телефона';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    // Проверка на pending withdrawal
    if (hasPendingWithdrawal) {
      showError('У вас уже есть заявка в обработке');
      return;
    }

    if (!validate()) {
      return;
    }

    setSubmitting(true);

    try {
      const details =
        method === 'card'
          ? {
              card_number: cardNumber.replace(/\s/g, ''),
              cardholder_name: cardholderName,
            }
          : {
              bank_name: bankName,
              phone_number: phoneNumber.replace(/\D/g, ''),
            };

      await apiService.createWithdrawal(Number(amount), method, details);

      showSuccess('Заявка отправлена на модерацию');
      onSuccess();
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Произошла ошибка');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Вывод средств">
      <div className="space-y-6">
        {/* Amount Section */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark">
              Сумма для вывода
            </label>
            <span className="text-sm text-text-muted dark:text-text-muted-dark">
              На балансе: {formatCurrency(balance)}
            </span>
          </div>
          <Input
            type="number"
            value={amount}
            onChange={setAmount}
            placeholder="Введите сумму"
            error={errors.amount}
          />
          <button
            onClick={handleWithdrawAll}
            className="text-primary text-sm font-medium mt-2 hover:underline"
          >
            Вывести всю сумму
          </button>
        </div>

        {/* Method Toggle */}
        <div>
          <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark mb-3">
            Способ вывода
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => setMethod('card')}
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                method === 'card'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              Банковская карта
            </button>
            <button
              onClick={() => setMethod('sbp')}
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                method === 'sbp'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              СБП
            </button>
          </div>
        </div>

        {/* Dynamic Fields */}
        {method === 'card' ? (
          <>
            <Input
              value={cardNumber}
              onChange={setCardNumber}
              label="Номер карты"
              placeholder="0000 0000 0000 0000"
              mask="card"
              error={errors.cardNumber}
            />
            <Input
              value={cardholderName}
              onChange={setCardholderName}
              label="ФИО получателя"
              placeholder="Иванов Иван Иванович"
              error={errors.cardholderName}
            />
          </>
        ) : (
          <>
            <div>
              <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark mb-2">
                Банк получателя
              </label>
              <select
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 font-display ${
                  errors.bankName
                    ? 'border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-600'
                } bg-white dark:bg-card-dark text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent`}
              >
                <option value="">Выберите банк</option>
                {BANKS.map((bank) => (
                  <option key={bank} value={bank}>
                    {bank}
                  </option>
                ))}
              </select>
              {errors.bankName && (
                <p className="mt-2 text-sm text-red-500">{errors.bankName}</p>
              )}
            </div>
            <Input
              type="tel"
              value={phoneNumber}
              onChange={setPhoneNumber}
              label="Номер телефона"
              placeholder="+7 (999) 999-99-99"
              mask="phone"
              error={errors.phoneNumber}
            />
          </>
        )}

        {/* Summary */}
        {amount && !errors.amount && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
            <p className="text-center text-lg font-semibold text-gray-900 dark:text-gray-100">
              К зачислению: {formatCurrency(Number(amount))}
            </p>
          </div>
        )}

        {/* Submit Button */}
        <Button
          variant="primary"
          fullWidth
          onClick={handleSubmit}
          loading={submitting}
          disabled={submitting}
        >
          Отправить заявку
        </Button>
      </div>
    </Modal>
  );
}
