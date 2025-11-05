import { logger } from './logger';

/**
 * Copies text to clipboard with fallback for older browsers and mobile WebViews
 * Uses textarea + execCommand method which is more reliable in Telegram WebView
 * @param text - Text to copy to clipboard
 * @throws Error if copying fails
 */
export async function copyToClipboard(text: string): Promise<void> {
  // Primary method: textarea + execCommand (most reliable in Telegram WebView)
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;

    // Styling for iOS compatibility
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';

    // Critical for iOS WebView
    textArea.setAttribute('readonly', '');
    textArea.contentEditable = 'true';
    textArea.readOnly = false;

    document.body.appendChild(textArea);

    // iOS-specific selection technique
    const range = document.createRange();
    range.selectNodeContents(textArea);

    const selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
      selection.addRange(range);
    }

    // Also try the standard way
    textArea.setSelectionRange(0, text.length);
    textArea.focus();
    textArea.select();

    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);

    if (successful) {
      logger.log('Copied to clipboard using execCommand');
      return;
    }

    throw new Error('execCommand("copy") returned false');
  } catch (error) {
    logger.warn('execCommand clipboard failed, trying modern API:', error);
  }

  // Fallback: Try modern Clipboard API
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      logger.log('Copied to clipboard using modern API');
      return;
    } catch (error) {
      logger.warn('Modern Clipboard API failed:', error);
    }
  }

  // All methods failed
  throw new Error('Failed to copy text to clipboard');
}
