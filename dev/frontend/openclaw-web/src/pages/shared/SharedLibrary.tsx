import { DownloadOutlined, SearchOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Empty,
  Input,
  Row,
  Select,
  Skeleton,
  Space,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useState, useMemo } from 'react';
import dayjs from 'dayjs';
import type { SharedResult } from '../../types';
import { sharedApi } from '../../api/shared';

const { Title, Text } = Typography;

const formatColors: Record<string, string> = {
  markdown: 'blue',
  json: 'geekblue',
  text: 'default',
  pdf: 'red',
  image: 'purple',
};

const SharedLibrary: React.FC = () => {
  const [items, setItems] = useState<SharedResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [filterFormat, setFilterFormat] = useState<string>('all');

  useEffect(() => {
    setLoading(true);
    sharedApi
      .list()
      .then((data) => {
        setItems(data as unknown as SharedResult[]);
      })
      .catch(() => {
        message.error('加载共享库失败');
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (filterFormat !== 'all' && item.output_format !== filterFormat) return false;
      if (searchText && !item.title?.toLowerCase().includes(searchText.toLowerCase())) return false;
      return true;
    });
  }, [items, filterFormat, searchText]);

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0 }}>📂 部门共享库</Title>
        <Text type="secondary">查看和下载本部门及跨部门分享的成果</Text>
      </div>

      <Card style={{ borderRadius: 12, marginBottom: 16 }} bodyStyle={{ padding: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={10}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索成果标题..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ borderRadius: 8 }}
            />
          </Col>
          <Col xs={12} sm={8}>
            <Select
              value={filterFormat}
              onChange={setFilterFormat}
              style={{ width: '100%' }}
              options={[
                { value: 'all', label: '全部格式' },
                { value: 'markdown', label: 'Markdown' },
                { value: 'json', label: 'JSON' },
                { value: 'text', label: 'Text' },
                { value: 'image', label: 'Image' },
              ]}
            />
          </Col>
          <Col xs={12} sm={6} style={{ textAlign: 'right' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>共 {filtered.length} 条</Text>
          </Col>
        </Row>
      </Card>

      {loading ? (
        <Row gutter={[16, 16]}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Col xs={24} sm={12} md={8} key={i}>
              <Card><Skeleton active /></Card>
            </Col>
          ))}
        </Row>
      ) : filtered.length === 0 ? (
        <Card style={{ borderRadius: 12 }}><Empty description="暂无共享成果" /></Card>
      ) : (
        <Row gutter={[16, 16]}>
          {filtered.map((item) => (
            <Col xs={24} sm={12} md={8} key={item.id}>
              <Card
                hoverable
                style={{ borderRadius: 12 }}
                bodyStyle={{ padding: 16 }}
                actions={[
                  <Button
                    type="link"
                    icon={<DownloadOutlined />}
                    key="download"
                    onClick={() => {
                      if (item.file_url) window.open(item.file_url, '_blank');
                    }}
                  >
                    下载
                  </Button>,
                ]}
              >
                <div style={{ marginBottom: 8 }}>
                  <Tag color={formatColors[item.output_format || 'text'] || 'default'}>
                    {(item.output_format || 'text').toUpperCase()}
                  </Tag>
                </div>
                <div style={{ fontWeight: 500, marginBottom: 8, fontSize: 14, minHeight: 40 }}>
                  {item.title || `成果 #${item.id.slice(0, 8)}`}
                </div>
                <Space size={12} wrap>
                  <Text style={{ fontSize: 12, color: '#888' }}>
                    🏢 {item.source_department_name || item.source_department_id}
                  </Text>
                  <Text style={{ fontSize: 12, color: '#888' }}>
                    🕐 {dayjs(item.created_at).format('MM-DD HH:mm')}
                  </Text>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default SharedLibrary;
