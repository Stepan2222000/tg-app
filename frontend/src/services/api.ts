import axios, { type AxiosInstance } from 'axios';
import { telegramService } from './telegram';
import { logger } from '../utils/logger';
import type {
  User,
  Task,
  TaskAssignment,
  Withdrawal,
  ReferralStats,
  Config,
  ApiResponse,
  TaskType,
  WithdrawalMethod,
  WithdrawalDetails,
  Screenshot,
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      // MOBILE-FRIENDLY: 60 seconds timeout for slower mobile networks
      // Mobile devices may have 2G/3G connections, so we need higher timeout
      timeout: 60000, // 60 seconds (increased from 30s for mobile support)
    });

    // Request interceptor to add Authorization header
    this.api.interceptors.request.use(
      (config) => {
        console.log('[DIAG] API Request:', config.method?.toUpperCase(), config.url);

        const initData = telegramService.getInitData();
        console.log('[DIAG] initData length before auth header:', initData?.length || 0);

        if (initData && initData.length > 0) {
          config.headers.Authorization = `tma ${initData}`;
          console.log('[DIAG] Authorization header added (length:', initData.length, ')');
        } else {
          console.error('[DIAG] ERROR: initData is empty! No Authorization header added!');
        }

        return config;
      },
      (error) => {
        console.error('[DIAG] Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => {
        console.log('[DIAG] API Response SUCCESS:', response.config.method?.toUpperCase(), response.config.url, 'Status:', response.status);
        return response.data;
      },
      (error) => {
        console.error('[DIAG] API Response ERROR:', error.config?.method?.toUpperCase(), error.config?.url, 'Status:', error.response?.status);
        console.error('[DIAG] Error details:', error.response?.data);
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
    console.log('[DIAG] === initUser() called ===');
    console.log('[DIAG] Timestamp:', new Date().toISOString());

    try {
      // CRITICAL FOR MOBILE: Wait for initData to be available before making request
      console.log('[DIAG] Waiting for initData with retry logic...');
      const initData = await telegramService.getInitDataWithRetry();
      console.log('[DIAG] initData obtained, length:', initData?.length || 0);

      if (!initData || initData.length === 0) {
        console.error('[DIAG] CRITICAL: initData still empty after retry!');
        throw new Error('Не удалось получить данные авторизации Telegram. Перезапустите приложение.');
      }

      // Make request with Authorization header (interceptor will use getInitData())
      const result = await this.api.post<never, User>('/api/auth/init');
      console.log('[DIAG] initUser() SUCCESS, user ID:', result.telegram_id);
      return result;
    } catch (error) {
      console.error('[DIAG] initUser() FAILED:', error);
      throw error;
    }
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
  ): Promise<Screenshot> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('assignment_id', assignmentId.toString());

    return this.api.post<never, Screenshot>(
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

  async getReferralList(): Promise<ReferralStats> {
    return this.api.get<never, ReferralStats>('/api/referrals/list');
  }
}

// Export singleton instance
export const apiService = new ApiService();
