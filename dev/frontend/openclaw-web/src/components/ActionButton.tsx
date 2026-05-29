import { Button, Modal } from 'antd';
import type { ButtonProps } from 'antd';
import { useState } from 'react';

interface ActionButtonProps extends Omit<ButtonProps, 'children'> {
  label: string;
  confirm?: string;
}

const ActionButton: React.FC<ActionButtonProps> = ({ label, loading, confirm, onClick, ...rest }) => {
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleClick = (e: React.MouseEvent<HTMLElement>) => {
    if (confirm) {
      setConfirmOpen(true);
    } else {
      onClick?.(e);
    }
  };

  const handleConfirm = (e: React.MouseEvent<HTMLElement>) => {
    setConfirmOpen(false);
    onClick?.(e);
  };

  return (
    <>
      <Button loading={loading} onClick={handleClick} {...rest}>
        {label}
      </Button>
      {confirm && (
        <Modal
          title="确认操作"
          open={confirmOpen}
          onOk={handleConfirm}
          onCancel={() => setConfirmOpen(false)}
          okText="确认"
          cancelText="取消"
          okButtonProps={{ danger: rest.danger }}
        >
          <p>{confirm}</p>
        </Modal>
      )}
    </>
  );
};

export default ActionButton;
