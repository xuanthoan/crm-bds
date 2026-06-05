import { ACTIVITY_LABELS, STATUS_LABELS } from '../constants';
import type { LeadActivity } from '../types';

function displayValue(value: string | null) { return value && value in STATUS_LABELS ? STATUS_LABELS[value as keyof typeof STATUS_LABELS] : value; }
export function LeadTimeline({ activities }: { activities: LeadActivity[] }) {
  if (!activities.length) return <div className="empty-state">Chưa có hoạt động nào.</div>;
  return <div className="lead-timeline">{activities.map((item) => <article key={item.id} className="timeline-item">
    <div className="timeline-marker" />
    <div><header><strong>{ACTIVITY_LABELS[item.activity_type]}</strong><time>{new Date(item.created_at).toLocaleString('vi-VN')}</time></header>
      {item.title && <h4>{item.title}</h4>}<p>{item.content}</p>
      {(item.old_value || item.new_value) && <div className="value-change">{displayValue(item.old_value)} → {displayValue(item.new_value)}</div>}
      <small>{item.user.full_name}</small>
    </div>
  </article>)}</div>;
}
