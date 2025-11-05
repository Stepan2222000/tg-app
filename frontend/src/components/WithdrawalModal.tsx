import { useState, useEffect } from 'react';
import { Modal } from './ui/Modal';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { Select } from './ui/Select';
import { MethodToggle } from './ui/MethodToggle';
import { apiService } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { formatCurrency } from '../utils/formatters';
import { validateAmount, validateCardNumber, validatePhone } from '../utils/validators';
import { logger } from '../utils/logger';
import type { WithdrawalMethod } from '../types';

interface WithdrawalModalProps {
  isOpen: boolean;
  onClose: () => void;
  balance: number;
  hasPendingWithdrawal: boolean;
  onSuccess: () => void;
}

const BANKS = [
  { value: 'Сбербанк', label: 'Сбербанк', icon: '🟢' },
  { value: 'Тинькофф', label: 'Тинькофф', icon: '🟡' },
  { value: 'Альфа-Банк', label: 'Альфа-Банк', icon: '🔴' },
  { value: 'ВТБ', label: 'ВТБ', icon: '🔵' },
  { value: 'Райффайзен', label: 'Райффайзен', icon: '🟠' },
  { value: 'Открытие', label: 'Открытие', icon: '🟣' },
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
        logger.error('Failed to load config:', error);
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
            icon="💰"
            disabled={submitting}
          />
          <button
            onClick={handleWithdrawAll}
            disabled={submitting}
            className="text-primary text-sm font-semibold mt-2 hover:underline transition-all hover:text-primary/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-base">rocket_launch</span>
            Вывести всю сумму
          </button>
        </div>

        {/* Method Toggle */}
        <div>
          <label className="block text-sm font-medium text-text-muted dark:text-text-muted-dark mb-3">
            Способ вывода
          </label>
          <MethodToggle method={method} onChange={setMethod} disabled={submitting} />
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
              disabled={submitting}
            />
            <Input
              value={cardholderName}
              onChange={setCardholderName}
              label="ФИО получателя"
              placeholder="Иванов Иван Иванович"
              error={errors.cardholderName}
              icon="👤"
              disabled={submitting}
            />
          </>
        ) : (
          <>
            <Select
              options={BANKS}
              value={bankName}
              onChange={setBankName}
              label="Банк получателя"
              placeholder="Выберите банк"
              error={errors.bankName}
              disabled={submitting}
            />
            <Input
              type="tel"
              value={phoneNumber}
              onChange={setPhoneNumber}
              label="Номер телефона"
              placeholder="+7 (999) 999-99-99"
              mask="phone"
              error={errors.phoneNumber}
              disabled={submitting}
            />
          </>
        )}

        {/* Summary */}
        {amount && !errors.amount && (
          <div className="bg-gradient-to-br from-primary/10 to-primary/5 dark:from-primary/20 dark:to-primary/10 rounded-2xl p-5 border border-primary/20 shadow-sm">
            <div className="flex items-center justify-center gap-2">
              <span className="text-2xl">✨</span>
              <div className="text-center">
                <p className="text-xs text-text-muted dark:text-text-muted-dark mb-1 font-medium">
                  К зачислению
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 tracking-tight">
                  {formatCurrency(Number(amount))}
                </p>
              </div>
              <span className="text-2xl">💎</span>
            </div>
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
