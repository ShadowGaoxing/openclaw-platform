import { Button, Typography } from 'antd';
import type { ReactNode } from 'react';

const { Title, Paragraph } = Typography;

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '64px 24px',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.6 }}>{icon}</div>
      <Title level={4} style={{ margin: '0 0 8px', color: '#495057' }}>
        {title}
      </Title>
      {description && (
        <Paragraph type="secondary" style={{ margin: '0 0 24px', maxWidth: 400 }}>
          {description}
        </Paragraph>
      )}
      {action && (
        <Button type="primary" onClick={action.onClick} style={{ borderRadius: 8 }}>
          {action.label}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
