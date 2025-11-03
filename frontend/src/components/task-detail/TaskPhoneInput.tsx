import { Input } from '../ui/Input';

interface TaskPhoneInputProps {
  value: string;
  onChange: (value: string) => void;
  error: string | null;
}

export function TaskPhoneInput({ value, onChange, error }: TaskPhoneInputProps) {
  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Подтверждение</h2>

      <p className="text-sm text-text-muted dark:text-text-muted-dark mb-4">
        Введите номер телефона продавца, который вы получили в переписке, для завершения задачи.
      </p>

      <Input
        type="tel"
        value={value}
        onChange={onChange}
        label="Номер телефона продавца"
        placeholder="+7 (999) 999-99-99"
        mask="phone"
        error={error || undefined}
      />
    </div>
  );
}
