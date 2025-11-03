import { Button } from '../ui/Button';

interface TaskActionsFooterProps {
  canSubmit: boolean;
  onSubmit: () => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

export function TaskActionsFooter({
  canSubmit,
  onSubmit,
  onCancel,
  isSubmitting,
}: TaskActionsFooterProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-background-light dark:bg-background-dark border-t border-gray-200 dark:border-gray-700 p-4 z-30">
      <div className="max-w-2xl mx-auto space-y-3">
        <Button
          variant="primary"
          fullWidth
          onClick={onSubmit}
          disabled={!canSubmit || isSubmitting}
          loading={isSubmitting}
        >
          Отправить на модерацию
        </Button>

        <Button
          variant="secondary"
          fullWidth
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Отказаться от задачи
        </Button>
      </div>
    </div>
  );
}
