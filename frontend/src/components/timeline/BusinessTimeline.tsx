import type { ReactNode } from 'react';

export type BusinessTimelineItem = {
  id: string;
  title: ReactNode;
  time?: ReactNode;
  actor?: ReactNode;
  description?: ReactNode;
  oldValue?: ReactNode;
  newValue?: ReactNode;
  meta?: ReactNode;
};

export function BusinessTimeline({ items, emptyText = 'Chưa có hoạt động.' }: { items: BusinessTimelineItem[]; emptyText?: string }) {
  if (!items.length) return <p className="empty-state">{emptyText}</p>;
  return <div className="business-timeline">{items.map((item) => <article className="business-timeline-item" key={item.id}>
    <span className="business-timeline-dot" />
    <div className="business-timeline-card">
      <header><h4>{item.title}</h4><p>{item.time || 'Chưa cập nhật'}{item.actor ? <> · {item.actor}</> : null}</p></header>
      {item.description ? <div className="business-timeline-description">{item.description}</div> : null}
      {(item.oldValue || item.newValue) ? <div className="business-timeline-change"><span>{item.oldValue || '—'}</span><b>→</b><span>{item.newValue || '—'}</span></div> : null}
      {item.meta ? <div className="business-timeline-meta">{item.meta}</div> : null}
    </div>
  </article>)}</div>;
}
