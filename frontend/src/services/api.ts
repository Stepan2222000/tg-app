import axios, { type AxiosInstance } from 'axios';
import { telegramService } from './telegram';
import { logger } from '../utils/logger';
import type {
  User,
  Task,
  TaskAssignment,
  Withdrawal,
  ReferralStats,
  Referral,
  Config,
  ApiResponse,
  TaskType,
  WithdrawalMethod,
  WithdrawalDetails,
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add Authorization header
    this.api.interceptors.request.use(
      (config) => {
        const initData = telegramService.getInitData();
        if (initData) {
          config.headers.Authorization = `tma ${initData}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response.data,
      (error) => {
        // NEW-CRITICAL-C FIX: Handle 401 (initData expired)
        if (error.response?.status === 401) {
          const message = error.response?.data?.detail || 'Сессия истекла';

          // Show Telegram alert and close app
          const tg = (window as any).Telegram?.WebApp;
          if (tg) {
            tg.showAlert(
              `${message}. Перезапустите приложение.`,
              () => {
                tg.close();
              }
            );
          } else {
            // Fallback for non-Telegram environment (development)
            logger.error('Session expired:', message);
            alert(`${message}. Перезапустите приложение.`);
          }

          return Promise.reject(new Error('Session expired'));
        }

        const errorMessage =
          error.response?.data?.detail || error.response?.data?.error || error.message || 'Произошла ошибка';
        logger.error('API Error:', errorMessage);
        return Promise.reject(new Error(errorMessage));
      }
    );
  }

  // Config
  async getConfig(): Promise<Config> {
    return this.api.get<never, Config>('/api/config');
  }

  // User
  async initUser(): Promise<User> {
    return this.api.post<never, User>('/api/auth/init');
  }

  async getUser(): Promise<User> {
    return this.api.get<never, User>('/api/user/me');
  }

  // Tasks
  async getAvailableTask(type: TaskType): Promise<Task> {
    return this.api.get<never, Task>(`/api/tasks/available?type=${type}`);
  }

  async getActiveTasks(): Promise<TaskAssignment[]> {
    return this.api.get<never, TaskAssignment[]>('/api/tasks/active');
  }

  async getTaskDetails(assignmentId: number): Promise<TaskAssignment> {
    return this.api.get<never, TaskAssignment>(`/api/tasks/${assignmentId}`);
  }

  async assignTask(taskId: number): Promise<TaskAssignment> {
    return this.api.post<never, TaskAssignment>(`/api/tasks/${taskId}/assign`);
  }

  async submitTask(
    assignmentId: number,
    phoneNumber?: string
  ): Promise<ApiResponse<void>> {
    return this.api.post<never, ApiResponse<void>>(
      `/api/tasks/${assignmentId}/submit`,
      { phone_number: phoneNumber }
    );
  }

  async cancelTask(assignmentId: number): Promise<ApiResponse<void>> {
    return this.api.post<never, ApiResponse<void>>(
      `/api/tasks/${assignmentId}/cancel`
    );
  }

  // Screenshots
  async uploadScreenshot(
    assignmentId: number,
    file: File
  ): Promise<{ screenshot_id: number }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('assignment_id', assignmentId.toString());

    return this.api.post<never, { screenshot_id: number }>(
      '/api/screenshots/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }

  async deleteScreenshot(screenshotId: number): Promise<ApiResponse<void>> {
    return this.api.delete<never, ApiResponse<void>>(
      `/api/screenshots/${screenshotId}`
    );
  }

  // Withdrawals
  async createWithdrawal(
    amount: number,
    method: WithdrawalMethod,
    details: WithdrawalDetails
  ): Promise<Withdrawal> {
    return this.api.post<never, Withdrawal>('/api/withdrawals', {
      amount,
      method,
      details,
    });
  }

  async getWithdrawalHistory(): Promise<Withdrawal[]> {
    return this.api.get<never, Withdrawal[]>('/api/withdrawals/history');
  }

  // Referrals
  async getReferralLink(): Promise<{ link: string }> {
    return this.api.get<never, { link: string }>('/api/referrals/link');
  }

  async getReferralStats(): Promise<ReferralStats> {
    return this.api.get<never, ReferralStats>('/api/referrals/stats');
  }

  async getReferralList(): Promise<Referral[]> {
    return this.api.get<never, Referral[]>('/api/referrals/list');
  }
}

// Export singleton instance
export const apiService = new ApiService();
