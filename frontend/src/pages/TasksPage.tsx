import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { TaskRequestSection } from '../components/tasks/TaskRequestSection';
import { ActiveTasksList } from '../components/tasks/ActiveTasksList';
import { TaskConfirmationModal } from '../components/tasks/TaskConfirmationModal';
import type { Config, TaskAssignment, TaskType } from '../types';

export function TasksPage() {
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();

  // Data state
  const [config, setConfig] = useState<Config | null>(null);
  const [activeTasks, setActiveTasks] = useState<TaskAssignment[]>([]);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isAssigning, setIsAssigning] = useState(false);

  // Modal state
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [selectedTaskType, setSelectedTaskType] = useState<TaskType | null>(null);

  // Load initial data
  const loadData = useCallback(async () => {
    try {
      const [configData, tasksData] = await Promise.all([
        apiService.getConfig(),
        apiService.getActiveTasks(),
      ]);

      setConfig(configData);
      setActiveTasks(tasksData);
    } catch (error) {
      console.error('Failed to load tasks data:', error);
      showError(
        error instanceof Error
          ? error.message
          : 'Не удалось загрузить данные. Попробуйте обновить страницу.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [showError]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // Silent refresh (no loading state)
      apiService.getActiveTasks().then(setActiveTasks).catch(console.error);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Handle request task button click
  const handleRequestTask = (type: TaskType) => {
    setSelectedTaskType(type);
    setConfirmModalOpen(true);
  };

  // Handle confirm task assignment
  const handleConfirmAssignment = async () => {
    if (!selectedTaskType) return;

    setIsAssigning(true);

    try {
      // Step 1: Get available task
      const task = await apiService.getAvailableTask(selectedTaskType);

      // Step 2: Assign task to user
      await apiService.assignTask(task.id);

      // Step 3: Refresh active tasks list
      const updatedTasks = await apiService.getActiveTasks();
      setActiveTasks(updatedTasks);

      // Success
      showSuccess('Задача получена! Выполните её в течение 24 часов');

      // Close modal
      setConfirmModalOpen(false);
      setSelectedTaskType(null);

      // Scroll to active tasks section
      setTimeout(() => {
        const activeTasksSection = document.getElementById('active-tasks');
        if (activeTasksSection) {
          activeTasksSection.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } catch (error) {
      console.error('Failed to assign task:', error);
      showError(
        error instanceof Error
          ? error.message
          : 'Не удалось получить задачу. Попробуйте ещё раз.'
      );
    } finally {
      setIsAssigning(false);
    }
  };

  // Handle cancel modal
  const handleCancelModal = () => {
    setConfirmModalOpen(false);
    setSelectedTaskType(null);
  };

  // Handle task card click
  const handleTaskClick = (assignmentId: number) => {
    navigate(`/tasks/${assignmentId}`);
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

  const maxActiveTasks = config?.max_active_tasks || 10;
  const simpleTaskPrice = config?.simple_task_price || 50;
  const phoneTaskPrice = config?.phone_task_price || 150;

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark font-display">
      <div className="max-w-2xl mx-auto p-4 space-y-6">
        {/* Header */}
        <header className="text-center py-4">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <span className="material-symbols-outlined text-2xl text-gray-600 dark:text-gray-400">
                arrow_back
              </span>
            </button>
            <h1 className="text-3xl font-black text-gray-900 dark:text-gray-100 flex-1">
              Работа с задачами
            </h1>
            <div className="w-10" /> {/* Spacer for centering */}
          </div>
        </header>

        {/* Task Request Section */}
        <TaskRequestSection
          activeTaskCount={activeTasks.length}
          maxActiveTasks={maxActiveTasks}
          simpleTaskPrice={simpleTaskPrice}
          phoneTaskPrice={phoneTaskPrice}
          onRequestTask={handleRequestTask}
          isLoading={isAssigning}
        />

        {/* Active Tasks Section */}
        <div id="active-tasks">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Активные задачи
          </h2>
          <ActiveTasksList tasks={activeTasks} onTaskClick={handleTaskClick} />
        </div>
      </div>

      {/* Confirmation Modal */}
      {selectedTaskType && (
        <TaskConfirmationModal
          isOpen={confirmModalOpen}
          taskType={selectedTaskType}
          price={selectedTaskType === 'phone' ? phoneTaskPrice : simpleTaskPrice}
          onConfirm={handleConfirmAssignment}
          onCancel={handleCancelModal}
          isLoading={isAssigning}
        />
      )}
    </div>
  );
}
