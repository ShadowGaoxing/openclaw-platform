import {
  AlertOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Modal,
  Form,
  Input,
  Row,
  Select,
  Skeleton,
  Tag,
  Tabs,
  message,
} from 'antd';
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import type { Task, TaskStatus } from '../../types';
import { tasksApi } from '../../api/tasks';
import { useAuthStore } from '../../store/authStore';
import { useTaskStore } from '../../store/taskStore';

const priorityConfig: Record<number, { color: string; label: string }> = {
  1: { color: '#ff4d4f', label: '紧急' },
  2: { color: '#faad14', label: '高优先' },
  3: { color: '#d9d9d9', label: '普通' },
  4: { color: '#d9d9d9', label: '低优先' },
  5: { color: '#d9d9d9', label: '低优先' },
};

const statusConfig: Record<TaskStatus, { color: string; label: string }> = {
  pending: { color: 'blue', label: '待领取' },
  claimed: { color: 'orange', label: '已领取' },
  assigned_auto: { color: 'purple', label: '已分配' },
  processing: { color: 'processing', label: '处理中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
  dead: { color: 'error', label: '死信' },
  suspected: { color: 'warning', label: '异常' },
};

const TaskList: React.FC = () => {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { tasks, total, activeTab, setActiveTab, setTasks } = useTaskStore();
  const [loading, setLoading] = useState(true);
  const [claimingId, setClaimingId] = useState<string | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm] = Form.useForm();
  const [creating, setCreating] = useState(false);

  const loadTasks = useCallback(async (tab: string) => {
    setLoading(true);
    try {
      const statusParam = tab === 'all' ? undefined : tab;
      const result = await tasksApi.list({
        status: statusParam,
        mine: tab !== 'all',
      });
      setTasks(result);
    } catch {
      message.error('加载任务失败');
    } finally {
      setLoading(false);
    }
  }, [setTasks]);

  useEffect(() => {
    loadTasks(activeTab);
  }, [activeTab, loadTasks]);

  const handleClaim = async (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    setClaimingId(taskId);
    try {
      await tasksApi.claim(taskId);
      message.success('任务已领取！请在 30 分钟内开始处理');
      await loadTasks(activeTab);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '领取失败，该任务可能已被其他人领取';
      message.warning(msg);
    } finally {
      setClaimingId(null);
    }
  };

  const handleCreate = async (values: Record<string, unknown>) => {
    setCreating(true);
    try {
      await tasksApi.create({
        title: values.title as string,
        description: values.description as string,
        department_id: user?.department_id || '',
        priority: Number(values.priority) || 3,
        assignment_strategy: (values.assignment_strategy as 'manual' | 'auto' | 'hybrid') || 'manual',
      });
      message.success('任务已创建');
      setCreateModalOpen(false);
      createForm.resetFields();
      await loadTasks(activeTab);
    } catch {
      message.error('创建任务失败');
    } finally {
      setCreating(false);
    }
  };

  const pendingCount = tasks.filter((t) => t.status === 'pending').length;

  return (
    <div>
      <div style={{ marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>📋 我的任务</h2>
          <p style={{ margin: '4px 0 0', color: '#888', fontSize: 14 }}>
            查看和领取待处理任务，跟踪执行进度
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          新建任务
        </Button>
      </div>

      <Card style={{ borderRadius: 12, marginBottom: 16 }} bodyStyle={{ padding: '0 0 12px 0' }}>
        <Tabs
          activeKey={activeTab}
          onChange={(k) => setActiveTab(k)}
          items={[
            { key: 'pending', label: <Badge count={pendingCount} size="small" offset={[6, 0]}>待领取</Badge> },
            { key: 'claimed', label: '已领取' },
            { key: 'processing', label: '处理中' },
            { key: 'completed', label: '已完成' },
            { key: 'all', label: '全部' },
          ]}
          style={{ paddingLeft: 16, marginBottom: 0 }}
        />
      </Card>

      {loading ? (
        <Row gutter={[0, 12]}>
          {[1, 2, 3].map((i) => (
            <Col xs={24} key={i}>
              <Card><Skeleton active paragraph={{ rows: 2 }} /></Card>
            </Col>
          ))}
        </Row>
      ) : tasks.length === 0 ? (
        <Card style={{ borderRadius: 12 }}>
          <Empty description="暂无任务" />
        </Card>
      ) : (
        <Row gutter={[0, 12]}>
          {tasks.map((task) => {
            const pConfig = priorityConfig[task.priority] || priorityConfig[3];
            const sConfig = statusConfig[task.status];

            return (
              <Col xs={24} key={task.id}>
                <Card
                  hoverable
                  style={{ borderRadius: 12, border: '1px solid #f0f0f0', transition: 'all 0.2s' }}
                  bodyStyle={{ padding: 16 }}
                  onClick={() => navigate(`/tasks/${task.id}`)}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <Tag color={pConfig.color} style={{ borderRadius: 4 }}>{pConfig.label}</Tag>
                        {task.status === 'pending' && (
                          <span style={{
                            width: 8, height: 8, borderRadius: '50%', background: '#52c41a',
                            display: 'inline-block', animation: 'pulse 2s infinite',
                          }} />
                        )}
                        <span style={{ fontSize: 16, fontWeight: 500, color: '#1a1a1a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {task.title}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: '#888', fontSize: 13 }}>
                        {task.recommended_model && (
                          <span><ThunderboltOutlined style={{ marginRight: 4 }} />{task.recommended_model}</span>
                        )}
                        <span>🏢 {task.department_name || task.department_id}</span>
                        <span><ClockCircleOutlined style={{ marginRight: 4 }} />{dayjs(task.created_at).format('MM-DD HH:mm')}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
                      {task.status === 'pending' ? (
                        <Button
                          type="primary"
                          icon={<AlertOutlined />}
                          style={{ borderRadius: 8 }}
                          loading={claimingId === task.id}
                          onClick={(e) => handleClaim(e, task.id)}
                        >
                          领取
                        </Button>
                      ) : (
                        <Tag color={sConfig.color} style={{ borderRadius: 4, margin: 0 }}>
                          {sConfig.label}
                          {task.status === 'processing' && task.progress_pct ? ` ${Math.round(task.progress_pct)}%` : ''}
                        </Tag>
                      )}
                    </div>
                  </div>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}

      {/* 新建任务弹窗 */}
      <Modal
        title="新建任务"
        open={createModalOpen}
        onCancel={() => { setCreateModalOpen(false); createForm.resetFields(); }}
        footer={null}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Form.Item name="title" label="任务标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="例如：Q2 市场调研报告分析" />
          </Form.Item>
          <Form.Item name="description" label="任务描述">
            <Input.TextArea rows={3} placeholder="详细说明任务要求..." />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={3}>
            <Select options={[
              { value: 1, label: '紧急 P1' },
              { value: 2, label: '高优先 P2' },
              { value: 3, label: '普通 P3' },
              { value: 4, label: '低优先 P4' },
            ]} />
          </Form.Item>
          <Form.Item name="assignment_strategy" label="分配策略" initialValue="manual">
            <Select options={[
              { value: 'manual', label: '手动领取' },
              { value: 'auto', label: '自动兜底（10分钟无人领取自动分配）' },
              { value: 'hybrid', label: '混合（手动为主，超时自动）' },
            ]} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={creating} block>
              创建任务
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TaskList;
