import { ACTIVITY_LABELS } from '../constants';
import type { DealActivity } from '../types';

function toneForTimelineValue(value?: string | null) {
  const text = (value || '').toLowerCase();
  if (!text) return 'muted';
  if (/(hủy|huỷ|thất bại|đã hủy|đã huỷ)/i.test(value || '')) return 'danger';
  if (/(hoàn tất|thành công|đã ký|có hiệu lực|đã thanh toán|contracted|won|completed|signed|active)/i.test(text)) return 'success';
  if (/(chờ|đã cọc|đặt cọc|dự kiến|ký hợp đồng|contract_pending|deposit|planned)/i.test(value || '')) return 'info';
  if (/(bản nháp|mới tạo|draft|new)/i.test(value || '')) return 'draft';
  return 'muted';
}

function TimelineValueBadge({ value }: { value?: string | null }) {
  return <span className={`deal-timeline-value-badge deal-timeline-value-badge--${toneForTimelineValue(value)}`}>{value || '—'}</span>;
}

export function DealTimeline({ activities = [] }: { activities?: DealActivity[] }) {
  return <div className="lead-timeline deal-timeline">{activities.map(a => <article className="timeline-item" key={a.id}><span className="timeline-marker"/><div><header><strong>{ACTIVITY_LABELS[a.activity_type as keyof typeof ACTIVITY_LABELS] || a.activity_type}</strong><time>{new Date(a.created_at).toLocaleString('vi-VN')}</time></header><h4>{a.title}</h4>{a.content && <p>{a.content}</p>}{(a.old_value || a.new_value) && <span className="value-change deal-timeline-transition"><TimelineValueBadge value={a.old_value}/><span className="deal-timeline-transition-arrow">→</span><TimelineValueBadge value={a.new_value}/></span>}<small>Người thực hiện: {a.user?.full_name || 'Người dùng hệ thống'}</small></div></article>)}{!activities.length && <p className="empty-state">Chưa có hoạt động.</p>}</div>;
}
