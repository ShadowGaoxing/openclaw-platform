import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
  ThunderboltOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Progress,
  Radio,
  Row,
  Space,
  Steps,
  Tag,
  Typography,
  message,
  Skeleton,
  Empty,
} from 'antd';
import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import type { Task } from '../../types';
import { tasksApi } from '../../api/tasks';
import { modelsApi } from '../../api/models';
import { useAuthStore } from '../../store/authStore';

const { Title, Text, Paragraph } = Typography;

interface ModelOption {
  id: string;
  model_name: string;
  cost_per_call: number;
  avg_latency_ms?: number;
  status: string;
}

const priorityLabel: Record<number, { color: string; label: string }> = {
  1: { color: 'red', label: '紧急 P1' },
  2: { color: 'orange', label: '高优先 P2' },
  3: { color: 'default', label: '普通 P3' },
  4: { color: 'default', label: '低优先 P4' },
};

const TaskDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const user = useAuthStore((s) => s.user);

  const [task, setTask] = useState<Task | null>(null);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [actionLoading, setActionLoading] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [t, m] = await Promise.all([
        tasksApi.get(id),
        modelsApi.list({ status_filter: 'online' }),
      ]);
      setTask(t);
      setModels(m.map((x) => ({
        id: x.id,
        model_name: x.model_name,
        cost_per_call: x.cost_per_call,
        avg_latency_ms: x.avg_latency_ms,
        status: x.status,
      })));
      setSelectedModel(t.override_model || t.recommended_model || (m[0]?.model_name ?? ''));
    } catch {
      message.error('加载任务详情失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
    // 进度轮询（MVP 简化版，未连 NATS WS 时的兜底）
    const interval = setInterval(() => {
      if (id) tasksApi.get(id).then(setTask).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [id, load]);

  const handleClaim = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await tasksApi.claim(id);
      message.success('已领取任务，请在 30 分钟内开始处理');
      await load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '领取失败';
      message.warning(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStart = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      if (selectedModel && selectedModel !== task?.recommended_model && selectedModel !== task?.override_model) {
        await tasksApi.overrideModel(id, selectedModel);
      }
      await tasksApi.start(id);
      message.success('任务已开始处理');
      await load();
    } catch {
      message.error('开始处理失败');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRelease = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await tasksApi.release(id);
      message.success('任务已释放回待领取池');
      await load();
    } catch {
      message.error('释放失败');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Card><Skeleton active paragraph={{ rows: 6 }} /></Card>
      </div>
    );
  }

  if (!task) {
    return <Empty description="任务不存在" />;
  }

  const currentModel = models.find((m) => m.model_name === selectedModel);
  const recommendedModel = models.find((m) => m.model_name === task.recommended_model);
  const isExpensive = currentModel && currentModel.cost_per_call > 0;

  const isOwner = task.assignee_id === user?.id;
  const pConfig = priorityLabel[task.priority] || priorityLabel[3];

  const currentStep = task.status === 'pending' ? 0
    : task.status === 'claimed' || task.status === 'assigned_auto' ? 1
    : task.status === 'processing' ? 2
    : task.status === 'completed' ? 3
    : 0;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={{ marginBottom: 8, color: '#666' }}>
          返回任务列表
        </Button>
        <Title level={4} style={{ margin: 0 }}>任务详情</Title>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card
            style={{ borderRadius: 12, marginBottom: 16 }}
            title={
              <Space>
                <Tag color={pConfig.color} style={{ borderRadius: 4 }}>{pConfig.label}</Tag>
                <span style={{ fontWeight: 500, fontSize: 16 }}>{task.title}</span>
              </Space>
            }
          >
            <Descriptions column={2} size="small">
              <Descriptions.Item label="🏢 部门">{task.department_name || task.department_id}</Descriptions.Item>
              <Descriptions.Item label="👤 创建人">{task.created_by || '—'}</Descriptions.Item>
              <Descriptions.Item label="⏰ 创建时间">{dayjs(task.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
              <Descriptions.Item label="🎯 分配策略">{task.assignment_strategy}</Descriptions.Item>
              <Descriptions.Item label="💰 推荐模型">
                {task.recommended_model || '系统自动路由'}
                {recommendedModel && recommendedModel.cost_per_call === 0 && (
                  <Tag color="green" style={{ marginLeft: 6 }}>免费</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="📌 状态"><Tag>{task.status}</Tag></Descriptions.Item>
            </Descriptions>

            {task.status === 'processing' && (
              <>
                <Divider style={{ margin: '12px 0' }} />
                <Progress percent={Math.round(task.progress_pct || 0)} status="active" />
              </>
            )}

            <Divider style={{ margin: '12px 0' }} />
            <Paragraph><Text strong>任务描述：</Text></Paragraph>
            <Paragraph style={{ color: '#555', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
              {task.description || '（无描述）'}
            </Paragraph>
          </Card>

          {/* 模型选择 — 决策 4 第二级覆盖 */}
          {(task.status === 'pending' || task.status === 'claimed') && (
            <Card
              style={{ borderRadius: 12 }}
              title="🤖 选择执行模型"
              extra={
                <Text style={{ color: '#888', fontSize: 12 }}>
                  默认：{task.recommended_model || '系统路由'}
                </Text>
              }
            >
              {models.length === 0 ? (
                <Empty description="暂无可用模型" />
              ) : (
                <Radio.Group value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} style={{ width: '100%' }}>
                  <Row gutter={[12, 12]}>
                    {models.map((model) => {
                      const isDefault = model.model_name === task.recommended_model;
                      const isFree = model.cost_per_call === 0;
                      return (
                        <Col xs={24} sm={12} md={8} key={model.id}>
                          <Card
                            hoverable
                            size="small"
                            style={{
                              borderRadius: 10,
                              border: selectedModel === model.model_name ? '2px solid #1677ff' : '1px solid #f0f0f0',
                              background: selectedModel === model.model_name ? '#e6f4ff' : '#fff',
                              cursor: 'pointer',
                            }}
                            onClick={() => setSelectedModel(model.model_name)}
                          >
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 14 }}>{model.model_name}</div>
                              <Space size={6}>
                                <Tag color={isFree ? 'green' : 'orange'}>
                                  {isFree ? '免费' : `¥${model.cost_per_call.toFixed(3)}/次`}
                                </Tag>
                                {model.avg_latency_ms ? (
                                  <Tag>~{Math.round(model.avg_latency_ms / 1000)}s</Tag>
                                ) : null}
                              </Space>
                              {isDefault && (
                                <div style={{ marginTop: 6 }}><Tag color="blue">推荐</Tag></div>
                              )}
                            </div>
                          </Card>
                        </Col>
                      );
                    })}
                  </Row>
                </Radio.Group>
              )}

              {isExpensive && (
                <div style={{ marginTop: 12, padding: '8px 12px', background: '#fff7e6', borderRadius: 8, border: '1px solid #ffd591', fontSize: 13, color: '#d46b08' }}>
                  ⚠️ 您选择了付费模型（¥{currentModel?.cost_per_call.toFixed(3)}/次），将产生额外费用。
                </div>
              )}
            </Card>
          )}
        </Col>

        <Col xs={24} lg={8}>
          <Card style={{ borderRadius: 12, marginBottom: 16 }} title="🎯 操作">
            {task.status === 'pending' && (
              <>
                <Button
                  type="primary"
                  size="large"
                  block
                  icon={<CheckCircleOutlined />}
                  loading={actionLoading}
                  onClick={handleClaim}
                  style={{ borderRadius: 8, height: 44, marginBottom: 12 }}
                >
                  确认领取任务
                </Button>
                <div style={{ padding: '8px 12px', background: '#f6ffed', borderRadius: 8, border: '1px solid #b7eb8f', fontSize: 12, color: '#389e0d' }}>
                  <ThunderboltOutlined style={{ marginRight: 4 }} />
                  领取后请在 30 分钟内开始处理，否则任务自动释放
                </div>
              </>
            )}
            {(task.status === 'claimed' || task.status === 'assigned_auto') && isOwner && (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  size="large"
                  block
                  icon={<PlayCircleOutlined />}
                  loading={actionLoading}
                  onClick={handleStart}
                  style={{ borderRadius: 8, height: 44 }}
                >
                  开始处理
                </Button>
                <Button block onClick={handleRelease} loading={actionLoading} style={{ borderRadius: 8 }}>
                  释放任务回池
                </Button>
              </Space>
            )}
            {task.status === 'processing' && (
              <div>
                <div style={{ marginBottom: 12 }}><Text strong>处理中...</Text></div>
                <Progress percent={Math.round(task.progress_pct || 0)} status="active" />
                <div style={{ marginTop: 8, fontSize: 12, color: '#888' }}>
                  Agent 自动处理中，请稍候。进度会自动刷新。
                </div>
              </div>
            )}
            {task.status === 'completed' && (
              <div>
                <Tag color="success" style={{ marginBottom: 8 }}><CheckCircleOutlined /> 已完成</Tag>
                {task.result_url && (
                  <Button type="link" icon={<UploadOutlined />} block href={task.result_url} target="_blank">
                    下载成果
                  </Button>
                )}
              </div>
            )}
          </Card>

          <Card style={{ borderRadius: 12 }} title="📊 执行进度">
            <Steps
              direction="vertical"
              size="small"
              current={currentStep}
              items={[
                { title: '领取任务', description: task.claimed_at ? dayjs(task.claimed_at).format('MM-DD HH:mm') : '点击领取' },
                { title: '开始处理', description: task.started_at ? dayjs(task.started_at).format('MM-DD HH:mm') : '领取后开始' },
                { title: '执行中', description: 'Agent 自动处理' },
                { title: '成果提交', description: task.completed_at ? dayjs(task.completed_at).format('MM-DD HH:mm') : '完成后自动回传' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TaskDetail;
