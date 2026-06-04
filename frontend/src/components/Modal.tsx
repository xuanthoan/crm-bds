import type { ReactNode } from 'react';

type ModalProps = {
  title: string;
  children?: ReactNode;
  onClose: () => void;
};

export function Modal({ title, children, onClose }: ModalProps) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-card" role="dialog" aria-modal="true">
        <header className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Đóng">
            ×
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
