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
    console.log('[DIAG] TelegramService.init() starting...');

    // Check if Telegram SDK is available
    const tg = (window as any).Telegram;
    if (!tg?.WebApp) {
      console.error('[DIAG] ERROR: window.Telegram.WebApp not found!');
      console.log('[DIAG] window.Telegram:', tg);
      throw new Error('Telegram WebApp SDK not available');
    }

    console.log('[DIAG] SDK found. Platform:', this.webApp.platform);
    console.log('[DIAG] SDK version:', this.webApp.version);
    console.log('[DIAG] initData length:', this.webApp.initData?.length || 0);
    console.log('[DIAG] initDataUnsafe.user:', this.webApp.initDataUnsafe.user ? 'present' : 'missing');
    console.log('[DIAG] initDataUnsafe.start_param:', this.webApp.initDataUnsafe.start_param || 'none');

    console.log('[DIAG] Calling webApp.ready()...');
    this.webApp.ready();

    console.log('[DIAG] Calling webApp.expand()...');
    this.webApp.expand();

    // Apply theme
    console.log('[DIAG] Applying theme...');
    this.applyTheme();

    console.log('[DIAG] TelegramService.init() completed successfully');
  }

  /**
   * Get initData string for backend authentication
   */
  getInitData(): string {
    const initData = this.webApp.initData;
    console.log('[DIAG] getInitData() called, length:', initData?.length || 0);

    if (!initData || initData.length === 0) {
      console.warn('[DIAG] WARNING: initData is empty or missing!');
    }

    return initData;
  }

  /**
   * Get user data from Telegram
   */
  getUserData(): TelegramUser | null {
    const user = this.webApp.initDataUnsafe.user;

    console.log('[DIAG] getUserData() called');

    if (!user) {
      console.error('[DIAG] ERROR: initDataUnsafe.user is missing!');
      return null;
    }

    console.log('[DIAG] User found - ID:', user.id, 'Username:', user.username || 'none', 'Name:', user.first_name);

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

  /**
   * Show copyable text via Telegram alert
   * Useful when clipboard API doesn't work in WebView
   */
  showCopyableText(text: string, message: string = 'Скопируйте ссылку:'): void {
    this.webApp.showAlert(`${message}\n\n${text}`);
  }
}

// Export singleton instance
export const telegramService = new TelegramService();
