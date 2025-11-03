import WebApp from '@twa-dev/sdk';

export interface TelegramUser {
  telegram_id: number;
  username?: string;
  first_name: string;
  referral_code?: string; // Extracted from start_param
}

class TelegramService {
  private webApp: typeof WebApp;

  constructor() {
    this.webApp = WebApp;
  }

  /**
   * Initialize Telegram WebApp
   */
  init(): void {
    this.webApp.ready();
    this.webApp.expand();

    // Apply theme
    this.applyTheme();
  }

  /**
   * Get initData string for backend authentication
   */
  getInitData(): string {
    return this.webApp.initData;
  }

  /**
   * Get user data from Telegram
   */
  getUserData(): TelegramUser | null {
    const user = this.webApp.initDataUnsafe.user;

    if (!user) {
      return null;
    }

    return {
      telegram_id: user.id,
      username: user.username,
      first_name: user.first_name,
      referral_code: this.getReferralCode(),
    };
  }

  /**
   * Extract referral code from start_param (format: ref_TELEGRAM_ID)
   */
  getReferralCode(): string | undefined {
    const startParam = this.webApp.initDataUnsafe.start_param;

    if (startParam && startParam.startsWith('ref_')) {
      return startParam.replace('ref_', '');
    }

    return undefined;
  }

  /**
   * Get current theme (light or dark)
   */
  getTheme(): 'light' | 'dark' {
    return this.webApp.colorScheme === 'dark' ? 'dark' : 'light';
  }

  /**
   * Apply Telegram theme to HTML element
   */
  applyTheme(): void {
    const theme = this.getTheme();

    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  /**
   * Show main button
   */
  showMainButton(text: string, onClick: () => void): void {
    this.webApp.MainButton.setText(text);
    this.webApp.MainButton.onClick(onClick);
    this.webApp.MainButton.show();
  }

  /**
   * Hide main button
   */
  hideMainButton(): void {
    this.webApp.MainButton.hide();
  }

  /**
   * Show back button
   */
  showBackButton(onClick: () => void): void {
    this.webApp.BackButton.onClick(onClick);
    this.webApp.BackButton.show();
  }

  /**
   * Hide back button
   */
  hideBackButton(): void {
    this.webApp.BackButton.hide();
  }

  /**
   * Open Telegram link
   */
  openTelegramLink(url: string): void {
    this.webApp.openTelegramLink(url);
  }

  /**
   * Open external link
   */
  openLink(url: string): void {
    this.webApp.openLink(url);
  }

  /**
   * Close Mini App
   */
  close(): void {
    this.webApp.close();
  }
}

// Export singleton instance
export const telegramService = new TelegramService();
