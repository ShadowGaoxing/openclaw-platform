import { Badge, Card, Tabs } from 'antd';
import type { TabsProps } from 'antd';

export interface TabItem {
  key: string;
  label: string;
  badge?: number;
}

interface TabBarProps {
  tabs: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
}

const TabBar: React.FC<TabBarProps> = ({ tabs, activeKey, onChange }) => {
  const items: TabsProps['items'] = tabs.map((tab) => ({
    key: tab.key,
    label: tab.badge !== undefined ? (
      <Badge count={tab.badge} size="small" offset={[6, 0]}>
        {tab.label}
      </Badge>
    ) : (
      tab.label
    ),
  }));

  return (
    <Card style={{ borderRadius: 12, marginBottom: 16 }} styles={{ body: { padding: '0 0 12px 0' } }}>
      <Tabs
        activeKey={activeKey}
        onChange={onChange}
        items={items}
        style={{ paddingLeft: 16, marginBottom: 0 }}
      />
    </Card>
  );
};

export default TabBar;
