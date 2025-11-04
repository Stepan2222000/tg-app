import { logger } from './logger';

/**
 * Copies text to clipboard with fallback for older browsers
 * @param text - Text to copy to clipboard
 * @throws Error if copying fails
 */
export async function copyToClipboard(text: string): Promise<void> {
  // Try modern Clipboard API first
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (error) {
      // If modern API fails, try fallback
      logger.warn('Clipboard API failed, trying fallback:', error);
    }
  }

  // Fallback for older browsers
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    textArea.style.top = '-9999px';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);

    if (!successful) {
      throw new Error('execCommand("copy") failed');
    }
  } catch (error) {
    throw new Error('Failed to copy text to clipboard');
  }
}
