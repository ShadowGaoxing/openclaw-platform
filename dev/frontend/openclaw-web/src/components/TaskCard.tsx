import { Card, Tag } from 'antd';
import { ClockCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Task } from '../types';
import StatusBadge from './StatusBadge';

interface TaskCardProps {
  task: Task;
  onClick?: () => void;
}

const PRIORITY_MAP: Record<number, { color: string; label: string }> = {
  1: { color: '#ff4d4f', label: '紧急' },
  2: { color: '#faad14', label: '高优先' },
  3: { color: '#d9d9d9', label: '普通' },
  4: { color: '#d9d9d9', label: '低优先' },
  5: { color: '#d9d9d9', label: '低优先' },
};

const TaskCard: React.FC<TaskCardProps> = ({ task, onClick }) => {
  const pConfig = PRIORITY_MAP[task.priority] || PRIORITY_MAP[3];
  const isPending = task.status === 'pending';

  return (
    <Card
      hoverable
      style={{
        borderRadius: 12,
        border: '1px solid #f0f0f0',
        transition: 'all 0.2s',
      }}
      styles={{ body: { padding: 16 } }}
      onClick={onClick}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Tag color={pConfig.color} style={{ borderRadius: 4, margin: 0 }}>{pConfig.label}</Tag>
            {isPending && (
              <span
                style={{
                  width: 8, height: 8, borderRadius: '50%', background: '#52c41a',
                  display: 'inline-block', animation: 'pulse 2s infinite',
                }}
              />
            )}
            <span
              style={{
                fontSize: 16, fontWeight: 500, color: '#1a1a1a',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}
            >
              {task.title}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: '#888', fontSize: 13 }}>
            {task.recommended_model && (
              <span><ThunderboltOutlined style={{ marginRight: 4 }} />{task.recommended_model}</span>
            )}
            <span>🏢 {task.department_name || task.department_id}</span>
            <span>
              <ClockCircleOutlined style={{ marginRight: 4 }} />
              {dayjs(task.created_at).format('MM-DD HH:mm')}
            </span>
          </div>
        </div>
        <div style={{ flexShrink: 0 }}>
          <StatusBadge status={task.status} />
          {task.status === 'processing' && task.progress_pct
            ? ` ${Math.round(task.progress_pct)}%`
            : ''}
        </div>
      </div>
    </Card>
  );
};

export default TaskCard;
