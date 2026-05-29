import React, { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100vh',
              padding: 40,
              fontFamily: 'system-ui, sans-serif',
              backgroundColor: '#f8f9fa',
            }}
          >
            <div style={{ fontSize: 56, marginBottom: 16 }}>🦾</div>
            <h2 style={{ color: '#ef4444', marginBottom: 8, margin: 0 }}>页面出现异常</h2>
            <p style={{ color: '#6c757d', marginBottom: 24, margin: '8px 0 24px' }}>
              请刷新页面重试，如果问题持续请联系管理员。
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 32px',
                borderRadius: 8,
                border: '1px solid #dee2e6',
                background: '#fff',
                cursor: 'pointer',
                fontSize: 14,
                color: '#212529',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#f1f3f5';
                e.currentTarget.style.borderColor = '#adb5bd';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#fff';
                e.currentTarget.style.borderColor = '#dee2e6';
              }}
            >
              刷新页面
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
