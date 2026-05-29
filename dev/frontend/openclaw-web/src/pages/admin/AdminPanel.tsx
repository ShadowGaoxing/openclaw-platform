import {
  BarChartOutlined,
  DesktopOutlined,
  KeyOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Empty,
  Row,
  Statistic,
  Table,
  Tag,
  Tabs,
  Typography,
  message,
  Skeleton,
} from 'antd';
import { useEffect, useState, useCallback } from 'react';
import { modelsApi } from '../../api/models';
import { agentsApi, type AgentItem } from '../../api/agents';
import { adminApi, type DashboardStats } from '../../api/admin';
import dayjs from 'dayjs';

const { Title } = Typography;

interface ModelRow {
  key: string;
  id: string;
  model_name: string;
  model_type: 'local' | 'api';
  deploy_location?: string;
  cost_per_call: number;
  status: string;
}

const modelColumns = [
  { title: '模型名称', dataIndex: 'model_name', key: 'name', render: (n: string) => <strong>{n}</strong> },
  { title: '类型', dataIndex: 'model_type', key: 'type', render: (t: string) => <Tag color={t === 'local' ? 'green' : 'blue'}>{t}</Tag> },
  { title: '部署位置', dataIndex: 'deploy_location', key: 'loc', render: (l: string) => l || '—' },
  { title: '单次成本', dataIndex: 'cost_per_call', key: 'cost', render: (c: number) => c === 0 ? <Tag color="green">免费</Tag> : `¥${c.toFixed(3)}` },
  { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => {
    const colors: Record<string, string> = { online: 'success', degraded: 'warning', offline: 'default' };
    return <Tag color={colors[s] || 'default'}>{s}</Tag>;
  }},
];

const agentColumns = [
  { title: 'Agent 名称', dataIndex: 'agent_name', key: 'name', render: (n: string) => <strong>{n}</strong> },
  { title: '部门', dataIndex: 'department_id', key: 'dept' },
  { title: '版本', dataIndex: 'version', key: 'version', render: (v?: string) => v || '—' },
  { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => {
    const colors: Record<string, string> = {
      online: 'success', offline: 'default', stale: 'error',
      reconnecting: 'processing', suspected_failure: 'warning',
    };
    return <Tag color={colors[s] || 'default'}>{s}</Tag>;
  }},
  { title: '并发', key: 'conc', render: (_: unknown, r: AgentItem) => `${r.current_concurrency}/${r.max_concurrency}` },
  { title: '最后心跳', dataIndex: 'last_seen_at', key: 'last_seen', render: (t?: string) => t ? dayjs(t).format('MM-DD HH:mm:ss') : '—' },
];

const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [models, setModels] = useState<ModelRow[]>([]);
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [s, m, a] = await Promise.all([
        adminApi.getStats().catch(() => null),
        modelsApi.list().catch(() => []),
        agentsApi.list().catch(() => []),
      ]);
      if (s) setStats(s);
      setModels(m.map((x) => ({ key: x.id, id: x.id, model_name: x.model_name, model_type: x.model_type, deploy_location: x.deploy_location, cost_per_call: x.cost_per_call, status: x.status })));
      setAgents(a);
    } catch {
      message.error('加载管理数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
    const t = setInterval(loadAll, 15000);  // 15s 自动刷新
    return () => clearInterval(t);
  }, [loadAll]);

  const tabItems = [
    {
      key: 'dashboard',
      label: <span><BarChartOutlined /> 数据看板</span>,
      children: loading ? <Skeleton active /> : stats ? (
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}><Card><Statistic title="总任务数" value={stats.total_tasks} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="待领取" value={stats.pending_tasks} valueStyle={{ color: '#1677ff' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="处理中" value={stats.processing_tasks} valueStyle={{ color: '#faad14' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="今日完成" value={stats.today_completed} valueStyle={{ color: '#52c41a' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="失败任务" value={stats.failed_tasks} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="死信任务" value={stats.dead_tasks} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="在线 Agent" value={stats.online_agents} valueStyle={{ color: '#52c41a' }} /></Card></Col>
          <Col xs={12} sm={6}><Card><Statistic title="疑似失联" value={stats.suspected_agents} valueStyle={{ color: '#faad14' }} /></Card></Col>
        </Row>
      ) : <Empty description="暂无数据" />,
    },
    {
      key: 'models',
      label: <span><DesktopOutlined /> 模型配置</span>,
      children: (
        <div>
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 500 }}>模型注册表（共 {models.length} 个）</span>
            <Button type="primary" size="small" onClick={loadAll}>刷新</Button>
          </div>
          <Table columns={modelColumns} dataSource={models} pagination={false} size="small" loading={loading} />
        </div>
      ),
    },
    {
      key: 'agents',
      label: <span><DesktopOutlined /> Agent 管理</span>,
      children: (
        <div>
          <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 500 }}>注册 Agent（共 {agents.length} 个）</span>
            <Button type="primary" size="small" onClick={loadAll}>刷新</Button>
          </div>
          <Table
            columns={agentColumns}
            dataSource={agents.map((a) => ({ ...a, key: a.id }))}
            pagination={false}
            size="small"
            loading={loading}
          />
        </div>
      ),
    },
    {
      key: 'lock',
      label: <span><KeyOutlined /> 部门锁定</span>,
      children: <Empty description="部门模型锁定配置（请在部门管理页设置）" />,
    },
    {
      key: 'quota',
      label: <span><TeamOutlined /> 配额设置</span>,
      children: <Empty description="部门配额（API 已就绪，UI 在 V1.1 完整开放）" />,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0 }}>⚙️ 管理后台</Title>
      </div>

      {/* 顶部统计卡片 */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card style={{ borderRadius: 12 }}>
              <Statistic title="在线 Agent" value={stats.online_agents} suffix={`/ ${stats.online_agents + stats.offline_agents + stats.suspected_agents}`} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card style={{ borderRadius: 12 }}><Statistic title="今日完成任务" value={stats.today_completed} /></Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card style={{ borderRadius: 12 }}><Statistic title="处理中任务" value={stats.processing_tasks} /></Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card style={{ borderRadius: 12 }}>
              <Statistic
                title="任务失败率"
                value={stats.total_tasks ? ((stats.failed_tasks + stats.dead_tasks) / stats.total_tasks * 100).toFixed(1) : '0.0'}
                suffix="%"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card style={{ borderRadius: 12 }} bodyStyle={{ padding: 0 }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{ padding: '0 16px' }}
          tabBarStyle={{ marginBottom: 0 }}
        />
      </Card>
    </div>
  );
};

export default AdminPanel;
