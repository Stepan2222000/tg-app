import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { Toast } from '../components/ui/Toast';

type NotificationType = 'success' | 'error' | 'info';

interface Notification {
  message: string;
  type: NotificationType;
  id: number;
}

interface NotificationContextType {
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showInfo: (message: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notification, setNotification] = useState<Notification | null>(null);
  const timeoutRef = useRef<number | undefined>(undefined);

  const showNotification = useCallback((message: string, type: NotificationType) => {
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const id = Date.now();
    setNotification({ message, type, id });

    // Автоматическое скрытие через 3 секунды
    timeoutRef.current = window.setTimeout(() => {
      setNotification((current) => (current?.id === id ? null : current));
    }, 3000);
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const showSuccess = useCallback(
    (message: string) => showNotification(message, 'success'),
    [showNotification]
  );

  const showError = useCallback(
    (message: string) => showNotification(message, 'error'),
    [showNotification]
  );

  const showInfo = useCallback(
    (message: string) => showNotification(message, 'info'),
    [showNotification]
  );

  const handleClose = useCallback(() => {
    setNotification(null);
  }, []);

  return (
    <NotificationContext.Provider value={{ showSuccess, showError, showInfo }}>
      {children}
      {notification && (
        <Toast
          message={notification.message}
          type={notification.type}
          onClose={handleClose}
        />
      )}
    </NotificationContext.Provider>
  );
}

export function useNotification(): NotificationContextType {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
}
