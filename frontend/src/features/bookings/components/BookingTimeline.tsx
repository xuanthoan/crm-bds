import type { BookingActivity, BookingActivityContext } from '../types';

const money = (value: string) => new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
}).format(Number(value));

const contextLabels: Array<[keyof BookingActivityContext, string, boolean]> = [
  ['booking_amount', 'Tiền giữ chỗ', true],
  ['deposit_amount', 'Tiền cọc', true],
  ['refund_amount', 'Số tiền hoàn', true],
  ['cancel_reason', 'Lý do hủy', false],
  ['refund_reason', 'Lý do hoàn tiền', false],
  ['note', 'Ghi chú', false],
];

function ActivityContext({ activity }: { activity: BookingActivity }) {
  const entries = contextLabels.filter(([key]) => activity.context?.[key]);
  if (!entries.length && activity.content) return <p><strong>Ghi chú:</strong> {activity.content}</p>;
  return <div className="booking-activity-context">
    {entries.map(([key, label, isMoney]) => {
      const value = activity.context[key]!;
      return <p key={key}><strong>{label}:</strong> {isMoney ? money(value) : value}</p>;
    })}
  </div>;
}

export function BookingTimeline({ activities }: { activities: BookingActivity[] }) {
  return <div className="lead-timeline">
    {activities.map((activity) => <article className="timeline-item" key={activity.id}>
      <span className="timeline-marker" />
      <div>
        <header><h4>{activity.title || activity.activity_label}</h4><time>{new Date(activity.created_at).toLocaleString('vi-VN')}</time></header>
        {(activity.old_value || activity.new_value) && <div className="value-change">{activity.old_value || '—'} → {activity.new_value || '—'}</div>}
        <ActivityContext activity={activity} />
        <small className="booking-activity-actor">Người thực hiện: {activity.actor.full_name}</small>
      </div>
    </article>)}
    {!activities.length && <p className="empty-state">Chưa có hoạt động.</p>}
  </div>;
}
