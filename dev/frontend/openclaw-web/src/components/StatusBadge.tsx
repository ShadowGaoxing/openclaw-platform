import { Tag } from 'antd';
import type { TaskStatus } from '../types';

interface StatusBadgeProps {
  status: TaskStatus;
  size?: 'sm' | 'md';
}

const STATUS_MAP: Record<TaskStatus, { color: string; label: string }> = {
  pending:       { color: 'blue',     label: '待领取' },
  claimed:       { color: 'orange',   label: '已领取' },
  assigned_auto: { color: 'purple',   label: '已分配' },
  processing:    { color: 'processing', label: '处理中' },
  completed:     { color: 'success',  label: '已完成' },
  failed:        { color: 'error',    label: '失败' },
  dead:          { color: 'error',    label: '死信' },
  suspected:     { color: 'warning',  label: '异常' },
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const config = STATUS_MAP[status] || { color: 'default', label: status };
  const fontSize = size === 'sm' ? 12 : 13;
  const padding = size === 'sm' ? '0 6px' : '0 8px';

  return (
    <Tag
      color={config.color}
      style={{ borderRadius: 4, margin: 0, fontSize, lineHeight: size === 'sm' ? '20px' : '22px', padding }}
    >
      {config.label}
    </Tag>
  );
};

export default StatusBadge;
