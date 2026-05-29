import {
  ApiOutlined,
  FolderOpenOutlined,
  KeyOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Button,
  Card,
  Form,
  Input,
  Menu,
  message,
  Typography,
} from 'antd';
import { useState } from 'react';
import { useAuthStore } from '../../store/authStore';

const { Title } = Typography;

const menuItems = [
  { key: 'profile', icon: <UserOutlined />, label: '个人资料' },
  { key: 'password', icon: <KeyOutlined />, label: '修改密码' },
  { key: 'agent', icon: <ApiOutlined />, label: 'Agent 配置' },
];

const Settings: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const [activeKey, setActiveKey] = useState('profile');
  const [profileForm] = Form.useForm();
  const [pwdForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const handleSaveProfile = async (values: { name?: string; email?: string }) => {
    setSaving(true);
    try {
      // PUT /api/v1/auth/profile (V1.1 功能，MVP 先写本地)
      updateUser({ name: values.name || user?.name, email: values.email || user?.email });
      message.success('个人资料已保存（本地）');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (values: { oldPassword: string; newPassword: string; confirmPassword: string }) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }
    setSaving(true);
    try {
      // TODO: POST /api/v1/auth/change-password (V1.1)
      message.success('密码修改功能将在 V1.1 上线');
      pwdForm.resetFields();
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAgent = (values: Record<string, string>) => {
    // Agent 配置存 localStorage（不入库，属于本地 Agent 配置）
    localStorage.setItem('agent_config', JSON.stringify(values));
    message.success('Agent 配置已保存（本地）');
  };

  const renderContent = () => {
    switch (activeKey) {
      case 'profile':
        return (
          <Form
            form={profileForm}
            layout="vertical"
            style={{ maxWidth: 480 }}
            initialValues={{ name: user?.name, email: user?.email, department: user?.department_name }}
            onFinish={handleSaveProfile}
          >
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Avatar size={80} icon={<UserOutlined />} style={{ backgroundColor: '#1677ff' }} src={user?.avatar} />
              <div style={{ marginTop: 8 }}>
                <Typography.Text type="secondary">{user?.role === 'admin' ? '系统管理员' : user?.role === 'dept_head' ? '部门主管' : '普通员工'}</Typography.Text>
              </div>
            </div>
            <Form.Item label="姓名" name="name">
              <Input style={{ borderRadius: 8 }} />
            </Form.Item>
            <Form.Item label="部门" name="department">
              <Input style={{ borderRadius: 8 }} disabled />
            </Form.Item>
            <Form.Item label="邮箱" name="email">
              <Input style={{ borderRadius: 8 }} type="email" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={saving} style={{ borderRadius: 8 }}>
              保存修改
            </Button>
          </Form>
        );
      case 'password':
        return (
          <Form form={pwdForm} layout="vertical" style={{ maxWidth: 480 }} onFinish={handleChangePassword}>
            <Form.Item label="当前密码" name="oldPassword" rules={[{ required: true }]}>
              <Input.Password style={{ borderRadius: 8 }} />
            </Form.Item>
            <Form.Item label="新密码" name="newPassword" rules={[{ required: true, min: 6 }]}>
              <Input.Password style={{ borderRadius: 8 }} />
            </Form.Item>
            <Form.Item label="确认新密码" name="confirmPassword" rules={[{ required: true }]}>
              <Input.Password style={{ borderRadius: 8 }} />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={saving} style={{ borderRadius: 8 }}>
              修改密码
            </Button>
          </Form>
        );
      case 'agent':
        return (
          <Form
            layout="vertical"
            style={{ maxWidth: 480 }}
            initialValues={(() => { try { return JSON.parse(localStorage.getItem('agent_config') || '{}'); } catch { return {}; } })()}
            onFinish={handleSaveAgent}
          >
            <Form.Item
              label={<span><FolderOpenOutlined style={{ marginRight: 4 }} /> 本地模型路径</span>}
              name="modelPath"
            >
              <Input style={{ borderRadius: 8 }} placeholder="~/.openclaw-agent/models/" />
            </Form.Item>
            <Form.Item label={<span><ApiOutlined style={{ marginRight: 4 }} /> OpenAI API Key</span>} name="openaiKey">
              <Input.Password style={{ borderRadius: 8 }} placeholder="sk-..." />
            </Form.Item>
            <Form.Item label="DeepSeek API Key" name="deepseekKey">
              <Input.Password style={{ borderRadius: 8 }} placeholder="sk-..." />
            </Form.Item>
            <Form.Item label="豆包 API Key" name="doubaoKey">
              <Input.Password style={{ borderRadius: 8 }} />
            </Form.Item>
            <Button type="primary" htmlType="submit" style={{ borderRadius: 8 }}>
              保存配置（本地）
            </Button>
          </Form>
        );
      default:
        return null;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0 }}>👤 个人设置</Title>
      </div>

      <Card style={{ borderRadius: 12 }} bodyStyle={{ padding: 0 }}>
        <div style={{ display: 'flex', minHeight: 400 }}>
          <div style={{ width: 200, borderRight: '1px solid #f0f0f0', padding: '16px 0' }}>
            <Menu
              mode="inline"
              selectedKeys={[activeKey]}
              onClick={({ key }) => setActiveKey(key)}
              items={menuItems}
              style={{ border: 'none' }}
            />
          </div>
          <div style={{ flex: 1, padding: 24 }}>
            {renderContent()}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Settings;
