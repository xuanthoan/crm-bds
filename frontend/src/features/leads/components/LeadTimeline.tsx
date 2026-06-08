import { ACTIVITY_LABELS, STATUS_LABELS } from '../constants';
import type { LeadActivity } from '../types';

function displayValue(value: string | null) { return value && value in STATUS_LABELS ? STATUS_LABELS[value as keyof typeof STATUS_LABELS] : value; }
function oldTimelineValue(item: LeadActivity) { return item.activity_type === 'assignment' ? item.old_owner_name ?? null : displayValue(item.old_value); }
function newTimelineValue(item: LeadActivity) { return item.activity_type === 'assignment' ? item.new_owner_name ?? null : displayValue(item.new_value); }
export function LeadTimeline({ activities }: { activities: LeadActivity[] }) {
  if (!activities.length) return <div className="empty-state">Chưa có hoạt động nào.</div>;
  return <div className="lead-timeline">{activities.map((item) => <article key={item.id} className="timeline-item">
    <div className="timeline-marker" />
    <div><header><strong>{ACTIVITY_LABELS[item.activity_type]}</strong><time>{new Date(item.created_at).toLocaleString('vi-VN')}</time></header>
      {item.title && <h4>{item.title}</h4>}<p>{item.content}</p>
      {(oldTimelineValue(item) || newTimelineValue(item)) && <div className="value-change">{oldTimelineValue(item)} → {newTimelineValue(item)}</div>}
      <small>{item.user.full_name}</small>
    </div>
  </article>)}</div>;
}
