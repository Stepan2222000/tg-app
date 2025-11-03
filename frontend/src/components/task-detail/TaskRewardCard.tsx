import { formatCurrency } from '../../utils/formatters';

interface TaskRewardCardProps {
  amount: number;
}

export function TaskRewardCard({ amount }: TaskRewardCardProps) {
  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
      <h2 className="text-center text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
        Вознаграждение
      </h2>
      <p className="text-center text-4xl font-black text-primary">{formatCurrency(amount)}</p>
    </div>
  );
}
