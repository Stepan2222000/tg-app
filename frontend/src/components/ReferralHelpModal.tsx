import { Modal } from './ui/Modal';
import { formatCurrency } from '../utils/formatters';

interface ReferralHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  commission: number; // 0.5 для 50%
}

export function ReferralHelpModal({ isOpen, onClose, commission }: ReferralHelpModalProps) {
  const commissionPercent = Math.round(commission * 100);
  const exampleEarning = 100;
  const exampleCommission = exampleEarning * commission;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Как работает программа">
      <div className="space-y-6">
        {/* Intro */}
        <div>
          <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100 mb-2">
            Реферальная программа
          </h3>
          <p className="text-text-muted dark:text-text-muted-dark leading-relaxed">
            Приглашайте друзей и получайте <span className="font-bold text-primary">{commissionPercent}%</span> от всех их заработков!
          </p>
        </div>

        {/* How it works */}
        <div>
          <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100 mb-3">
            Как это работает?
          </h3>
          <ol className="space-y-3">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary rounded-full flex items-center justify-center text-sm font-bold">
                1
              </span>
              <span className="text-text-muted dark:text-text-muted-dark">
                Скопируйте вашу реферальную ссылку
              </span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary rounded-full flex items-center justify-center text-sm font-bold">
                2
              </span>
              <span className="text-text-muted dark:text-text-muted-dark">
                Поделитесь ей с друзьями в мессенджерах или соцсетях
              </span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary rounded-full flex items-center justify-center text-sm font-bold">
                3
              </span>
              <span className="text-text-muted dark:text-text-muted-dark">
                Когда друг регистрируется по вашей ссылке, он становится вашим рефералом
              </span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary/20 text-primary rounded-full flex items-center justify-center text-sm font-bold">
                4
              </span>
              <span className="text-text-muted dark:text-text-muted-dark">
                За каждую выполненную им задачу вы получаете <span className="font-semibold text-primary">{commissionPercent}%</span> комиссии
              </span>
            </li>
          </ol>
        </div>

        {/* Example */}
        <div className="bg-primary/10 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-primary text-xl">
              calculate
            </span>
            <h4 className="font-bold text-gray-900 dark:text-gray-100">
              Пример расчета
            </h4>
          </div>
          <p className="text-sm text-gray-900 dark:text-gray-100">
            Ваш друг заработал <span className="font-bold">{formatCurrency(exampleEarning)}</span> →
            вы получаете <span className="font-bold text-primary">{formatCurrency(exampleCommission)}</span>
          </p>
        </div>

        {/* Benefits */}
        <div className="bg-card-light dark:bg-card-dark border-2 border-primary/20 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-primary text-2xl flex-shrink-0">
              tips_and_updates
            </span>
            <div>
              <h4 className="font-bold text-gray-900 dark:text-gray-100 mb-1">
                Без ограничений!
              </h4>
              <p className="text-sm text-text-muted dark:text-text-muted-dark">
                Приглашайте неограниченное количество друзей. Чем больше рефералов работает, тем больше вы зарабатываете.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}
