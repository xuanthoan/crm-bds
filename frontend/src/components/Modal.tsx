import { useEffect, useId, useRef, type MouseEvent, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

type ModalProps = {
  title: string;
  children?: ReactNode;
  onClose: () => void;
};

type BodyState = {
  overflow: string;
  pointerEvents: string;
};

let openModalCount = 0;
let originalBodyState: BodyState | null = null;

function lockPage(): void {
  if (openModalCount === 0) {
    originalBodyState = {
      overflow: document.body.style.overflow,
      pointerEvents: document.body.style.pointerEvents,
    };
    document.body.style.overflow = 'hidden';
    document.body.style.pointerEvents = '';
    document.body.classList.add('modal-open');
  }
  openModalCount += 1;
}

function unlockPage(): void {
  openModalCount = Math.max(0, openModalCount - 1);
  if (openModalCount > 0) return;

  document.body.style.overflow = originalBodyState?.overflow ?? '';
  document.body.style.pointerEvents = originalBodyState?.pointerEvents === 'none' ? '' : (originalBodyState?.pointerEvents ?? '');
  document.body.classList.remove('modal-open');
  originalBodyState = null;
}

export function Modal({ title, children, onClose }: ModalProps) {
  const titleId = useId();
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    lockPage();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onCloseRef.current();
    }

    function handleRouteChange() {
      onCloseRef.current();
    }

    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('popstate', handleRouteChange);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('popstate', handleRouteChange);
      unlockPage();
    };
  }, []);

  function handleBackdropClick(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) onClose();
  }

  return createPortal(
    <div className="modal-backdrop" data-modal-backdrop="true" role="presentation" onMouseDown={handleBackdropClick}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <header className="modal-header">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Đóng">
            ×
          </button>
        </header>
        {children}
      </section>
    </div>,
    document.body,
  );
}
