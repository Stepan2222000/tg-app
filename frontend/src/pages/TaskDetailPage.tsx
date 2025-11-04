import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiService } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { validatePhone } from '../utils/validators';
import { generateDisplayId } from '../utils/taskHelpers';
import { logger } from '../utils/logger';
import { TaskHeader } from '../components/task-detail/TaskHeader';
import { TaskTimerCard } from '../components/task-detail/TaskTimerCard';
import { TaskRewardCard } from '../components/task-detail/TaskRewardCard';
import { TaskInstructionsCard } from '../components/task-detail/TaskInstructionsCard';
import { TaskMessageCard } from '../components/task-detail/TaskMessageCard';
import { TaskPhoneInput } from '../components/task-detail/TaskPhoneInput';
import { TaskScreenshotsUpload } from '../components/task-detail/TaskScreenshotsUpload';
import { TaskSubmissionChecklist } from '../components/task-detail/TaskSubmissionChecklist';
import { TaskActionsFooter } from '../components/task-detail/TaskActionsFooter';
import { Modal } from '../components/ui/Modal';
import type { Config, TaskAssignment, Screenshot } from '../types';

export function TaskDetailPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  const { showSuccess, showError, showInfo } = useNotification();

  // Data state
  const [assignment, setAssignment] = useState<TaskAssignment | null>(null);
  const [config, setConfig] = useState<Config | null>(null);

  // Form state
  const [phoneNumber, setPhoneNumber] = useState('');
  const [screenshots, setScreenshots] = useState<Screenshot[]>([]);
  const [phoneError, setPhoneError] = useState<string | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);

  // NEW-CRITICAL FIX: Ref for synchronous deduplication
  // useState is async, so double-clicks can bypass isSubmitting check
  const submitInProgressRef = useRef(false);

  // Load data
  useEffect(() => {
    if (!assignmentId) {
      showError('ID задачи не найден');
      navigate('/tasks');
      return;
    }

    const loadData = async () => {
      try {
        const [assignmentData, configData] = await Promise.all([
          apiService.getTaskDetails(parseInt(assignmentId)),
          apiService.getConfig(),
        ]);

        // Check if task already submitted
        if (assignmentData.status !== 'assigned') {
          showInfo('Задача уже отправлена');
          navigate('/tasks');
          return;
        }

        setAssignment(assignmentData);
        setConfig(configData);

        // Initialize screenshots from assignment
        if (assignmentData.screenshots && assignmentData.screenshots.length > 0) {
          setScreenshots(assignmentData.screenshots);
        }

        // Initialize phone number if exists
        if (assignmentData.phone_number) {
          setPhoneNumber(assignmentData.phone_number);
        }
      } catch (error) {
        logger.error('Failed to load task details:', error);
        showError(
          error instanceof Error
            ? error.message
            : 'Не удалось загрузить задачу'
        );
        navigate('/tasks');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [assignmentId, navigate, showError, showInfo]);

  // Computed values
  const taskType = assignment?.task?.type || 'simple';
  const requiresPhoneNumber = taskType === 'phone';
  const hasScreenshots = screenshots.length > 0;
  const hasValidPhone = requiresPhoneNumber
    ? Boolean(phoneNumber) && validatePhone(phoneNumber)
    : true;
  const canSubmit = hasScreenshots && hasValidPhone && !isSubmitting;

  // Get reward amount
  const rewardAmount =
    taskType === 'simple'
      ? config?.simple_task_price || 50
      : config?.phone_task_price || 150;

  // Get incomplete requirements for checklist
  const getIncompleteRequirements = (): string[] => {
    const requirements: string[] = [];

    if (!hasScreenshots) {
      requirements.push('Загрузите хотя бы 1 скриншот');
    }

    if (requiresPhoneNumber && !phoneNumber) {
      requirements.push('Введите номер телефона');
    }

    if (requiresPhoneNumber && phoneNumber && !validatePhone(phoneNumber)) {
      requirements.push('Номер телефона некорректен');
    }

    return requirements;
  };

  // Handle phone number change
  const handlePhoneChange = (value: string) => {
    setPhoneNumber(value);
    // Validate immediately
    if (requiresPhoneNumber && value && !validatePhone(value)) {
      setPhoneError('Введите корректный номер телефона');
    } else {
      setPhoneError(null);
    }
  };

  // Handle submit
  const handleSubmit = async () => {
    if (!assignment || !canSubmit) return;

    // NEW-CRITICAL FIX: Synchronous deduplication check
    // Prevents double-submit from double-click
    if (submitInProgressRef.current) {
      logger.warn('Submit already in progress, ignoring duplicate request');
      return;
    }

    // Final validation
    if (requiresPhoneNumber && !validatePhone(phoneNumber)) {
      setPhoneError('Введите корректный номер телефона');
      showError('Проверьте правильность номера телефона');
      return;
    }

    // Mark request as in-progress (synchronous)
    submitInProgressRef.current = true;
    setIsSubmitting(true);

    try {
      await apiService.submitTask(
        assignment.id,
        requiresPhoneNumber ? phoneNumber : undefined
      );

      showSuccess('Задача отправлена на модерацию (~2 часа)');
      navigate('/tasks');
    } catch (error) {
      logger.error('Failed to submit task:', error);
      showError(
        error instanceof Error ? error.message : 'Не удалось отправить задачу'
      );
    } finally {
      // Reset both state and ref
      submitInProgressRef.current = false;
      setIsSubmitting(false);
    }
  };

  // Handle cancel
  const handleCancelClick = () => {
    setCancelModalOpen(true);
  };

  const handleConfirmCancel = async () => {
    if (!assignment) return;

    try {
      await apiService.cancelTask(assignment.id);
      showInfo('Задача отменена');
      navigate('/tasks');
    } catch (error) {
      logger.error('Failed to cancel task:', error);
      showError(
        error instanceof Error ? error.message : 'Не удалось отменить задачу'
      );
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark flex items-center justify-center">
        <span className="material-symbols-outlined text-5xl text-primary animate-spin">
          progress_activity
        </span>
      </div>
    );
  }

  if (!assignment || !assignment.task) {
    return null;
  }

  const displayId = generateDisplayId(assignment.id);
  const instructions = config?.instructions || '';

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark font-display pb-36">
      {/* Header */}
      <TaskHeader taskId={displayId} onBack={() => navigate('/tasks')} />

      {/* Content */}
      <div className="max-w-2xl mx-auto p-4 space-y-4">
        {/* Timer Card */}
        <TaskTimerCard
          taskType={taskType}
          deadline={assignment.deadline}
          assignedAt={assignment.assigned_at}
        />

        {/* Reward Card */}
        <TaskRewardCard amount={rewardAmount} />

        {/* Instructions Card */}
        <TaskInstructionsCard
          instructions={instructions}
          avitoUrl={assignment.task.avito_url}
        />

        {/* Message Card */}
        <TaskMessageCard messageText={assignment.task.message_text} />

        {/* Phone Input (only for phone tasks) */}
        {requiresPhoneNumber && (
          <TaskPhoneInput
            value={phoneNumber}
            onChange={handlePhoneChange}
            error={phoneError}
          />
        )}

        {/* Screenshots Upload */}
        <TaskScreenshotsUpload
          assignmentId={assignment.id}
          screenshots={screenshots}
          onScreenshotsChange={setScreenshots}
          maxScreenshots={5}
        />

        {/* Submission Checklist */}
        <TaskSubmissionChecklist
          requirements={getIncompleteRequirements()}
        />
      </div>

      {/* Actions Footer */}
      <TaskActionsFooter
        canSubmit={canSubmit}
        onSubmit={handleSubmit}
        onCancel={handleCancelClick}
        isSubmitting={isSubmitting}
      />

      {/* Cancel Confirmation Modal */}
      <Modal
        isOpen={cancelModalOpen}
        onClose={() => setCancelModalOpen(false)}
        title="Отказаться от задачи?"
      >
        <div className="space-y-4">
          <p className="text-center text-text-muted dark:text-text-muted-dark">
            Вы уверены, что хотите отказаться от этой задачи? Вы сможете взять новую задачу.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => setCancelModalOpen(false)}
              className="flex-1 py-3 px-4 rounded-xl font-semibold bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Отмена
            </button>
            <button
              onClick={handleConfirmCancel}
              className="flex-1 py-3 px-4 rounded-xl font-semibold bg-red-500 text-white hover:bg-red-600 transition-colors"
            >
              Отказаться
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
