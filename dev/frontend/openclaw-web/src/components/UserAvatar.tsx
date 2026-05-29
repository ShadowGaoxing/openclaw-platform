import { Avatar, Tooltip } from 'antd';

interface UserAvatarProps {
  name: string;
  avatar?: string;
  online?: boolean;
  size?: number;
}

const COLORS = [
  '#364fc7', '#e8590c', '#2f9e44', '#e64980',
  '#0c8599', '#6741d9', '#f59f00', '#c2255c',
];

function getColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return COLORS[Math.abs(hash) % COLORS.length];
}

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

const UserAvatar: React.FC<UserAvatarProps> = ({ name, avatar, online, size = 32 }) => {
  const content = avatar ? (
    <Avatar src={avatar} size={size} />
  ) : (
    <Avatar
      size={size}
      style={{
        backgroundColor: getColor(name),
        verticalAlign: 'middle',
        fontSize: size * 0.4,
        fontWeight: 600,
      }}
    >
      {getInitials(name)}
    </Avatar>
  );

  return (
    <Tooltip title={name}>
      <div style={{ position: 'relative', display: 'inline-flex' }}>
        {content}
        {online !== undefined && (
          <span
            style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: size * 0.3,
              height: size * 0.3,
              borderRadius: '50%',
              border: `2px solid #fff`,
              background: online ? '#52c41a' : '#d9d9d9',
            }}
          />
        )}
      </div>
    </Tooltip>
  );
};

export default UserAvatar;
