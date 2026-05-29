import { BellOutlined, SettingOutlined, UserOutlined, WarningOutlined } from '@ant-design/icons';
import { Alert, Avatar, Badge, Dropdown, Layout, Space } from 'antd';
import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useTaskStore } from '../store/taskStore';
import { authApi } from '../api/auth';
import apiClient from '../api/client';

const { Header, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

type ConnStatus = 'ok' | 'degraded' | 'failed';

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const unreadCount = useTaskStore((s) => s.unreadCount);
  const [connStatus, setConnStatus] = useState<ConnStatus>('ok');

  const isAdmin = user?.role === 'admin' || user?.role === 'dept_head';

  const navItems = [
    { key: '/', label: '📋 我的任务' },
    { key: '/shared', label: '📂 部门共享库' },
    ...(isAdmin ? [{ key: '/admin', label: '⚙️ 管理后台' }] : []),
    { key: '/settings', label: '👤 个人设置' },
  ];

  // 健康探活（兜底，WS 未启用时仍能感知连接状态）— PRD §10.5
  useEffect(() => {
    let failures = 0;
    const check = async () => {
      try {
        await apiClient.get('/auth/profile', { timeout: 5000 });
        failures = 0;
        setConnStatus('ok');
      } catch {
        failures += 1;
        if (failures >= 3) setConnStatus('failed');
        else setConnStatus('degraded');
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleUserMenuClick = async ({ key }: { key: string }) => {
    if (key === 'logout') {
      await authApi.logout();
      logout();
      navigate('/login');
    } else if (key === 'settings') {
      navigate('/settings');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <div
            style={{ fontSize: 18, fontWeight: 700, color: '#1677ff', cursor: 'pointer', whiteSpace: 'nowrap' }}
            onClick={() => navigate('/')}
          >
            🦾 OpenCLAW
          </div>
          <nav style={{ display: 'flex', gap: 4 }}>
            {navItems.map((item) => (
              <a
                key={item.key}
                onClick={() => navigate(item.key)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  fontSize: 14,
                  color: location.pathname === item.key ? '#1677ff' : '#666',
                  background: location.pathname === item.key ? '#e6f4ff' : 'transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textDecoration: 'none',
                }}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>

        <Space size={20}>
          <Badge count={unreadCount} size="small" offset={[-2, 2]}>
            <BellOutlined style={{ fontSize: 20, color: '#666', cursor: 'pointer' }} />
          </Badge>

          <Dropdown
            menu={{
              items: [
                { key: 'profile', label: user?.name || user?.email || '未登录', disabled: true },
                { type: 'divider' },
                { key: 'settings', label: '个人设置', icon: <SettingOutlined /> },
                { type: 'divider' },
                { key: 'logout', label: '退出登录', danger: true },
              ],
              onClick: handleUserMenuClick,
            }}
            placement="bottomRight"
          >
            <Avatar
              size={32}
              icon={<UserOutlined />}
              style={{ backgroundColor: '#1677ff', cursor: 'pointer' }}
              src={user?.avatar}
            />
          </Dropdown>
        </Space>
      </Header>

      {/* WS / 后端连接状态横幅（PRD §10.5） */}
      {connStatus === 'degraded' && (
        <Alert
          message="连接异常，正在重试…"
          description="实时数据可能有延迟，刷新数据可能失败。"
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          banner
          closable
        />
      )}
      {connStatus === 'failed' && (
        <Alert
          message="无法连接到服务器"
          description="请检查网络后刷新页面。"
          type="error"
          showIcon
          banner
        />
      )}

      <Content style={{ padding: '24px', background: '#f5f5f5' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>{children}</div>
      </Content>
    </Layout>
  );
};

export default MainLayout;
