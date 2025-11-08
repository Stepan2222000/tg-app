import { Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';
import { logger } from '../utils/logger';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component to catch unhandled errors in React component tree.
 * Falls back to error UI when a rendering error occurs.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to console/monitoring service
    logger.error('Error Boundary caught an error:', error);
    logger.error('Error Info:', errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    // Reload the page to restart the app
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-[#1a1a1a] text-white px-4">
          <div className="text-center max-w-md">
            <div className="text-red-500 text-5xl mb-4">💥</div>
            <h2 className="text-xl font-bold mb-2">Что-то пошло не так</h2>
            <p className="text-gray-400 mb-6">
              Произошла неожиданная ошибка. Пожалуйста, перезапустите приложение.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <details className="text-left mb-6 bg-gray-800 p-4 rounded-lg">
                <summary className="cursor-pointer text-sm font-medium mb-2">
                  Детали ошибки (только для разработки)
                </summary>
                <pre className="text-xs text-red-300 overflow-auto max-h-40">
                  {this.state.error.toString()}
                  {this.state.errorInfo && (
                    <>
                      {'\n\n'}
                      {this.state.errorInfo.componentStack}
                    </>
                  )}
                </pre>
              </details>
            )}

            <button
              onClick={this.handleReset}
              className="bg-[#C9A87C] text-black px-6 py-3 rounded-lg font-semibold hover:bg-[#b8976b] transition-colors"
            >
              Перезапустить приложение
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
