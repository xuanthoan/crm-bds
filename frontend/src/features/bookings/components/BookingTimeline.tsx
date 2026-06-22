import type { BookingActivity, BookingActivityContext } from '../types';

const money = (value: string) => new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
}).format(Number(value));

const statusPresentation: Record<string, { title: string; modifier: string }> = {
  'Mới tạo': { title: 'Mới tạo', modifier: 'draft' },
  'Đã giữ chỗ': { title: 'Giữ chỗ', modifier: 'reserved' },
  'Đã cọc': { title: 'Đặt cọc', modifier: 'deposited' },
  'Đã hủy': { title: 'Hủy booking', modifier: 'cancelled' },
  'Hết hạn giữ chỗ': { title: 'Hết hạn giữ chỗ', modifier: 'expired' },
  'Đã hoàn tiền': { title: 'Hoàn tiền', modifier: 'refunded' },
};

const contextLabels: Array<[keyof BookingActivityContext, string, boolean]> = [
  ['booking_amount', 'Tiền giữ chỗ', true],
  ['deposit_amount', 'Tiền cọc', true],
  ['refund_amount', 'Số tiền hoàn', true],
  ['deduction_amount', 'Khấu trừ', true],
  ['cancel_reason', 'Lý do hủy', false],
  ['refund_reason', 'Lý do hoàn tiền', false],
  ['deduction_reason', 'Lý do khấu trừ', false],
  ['note', 'Ghi chú', false],
];

function activityTitle(activity: BookingActivity) {
  if (activity.new_value && statusPresentation[activity.new_value]) {
    return statusPresentation[activity.new_value].title;
  }
  return activity.title || activity.activity_label;
}

function StatusBadge({ label }: { label: string }) {
  const modifier = statusPresentation[label]?.modifier;
  const className = modifier
    ? `booking-timeline-status-badge booking-timeline-status-badge--${modifier}`
    : 'booking-timeline-status-badge';
  return <span className={className}>{label}</span>;
}

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
        <header><h4>{activityTitle(activity)}</h4><time>{new Date(activity.created_at).toLocaleString('vi-VN')}</time></header>
        {(activity.old_value || activity.new_value) && <div className="booking-timeline-transition">
          {activity.old_value ? <StatusBadge label={activity.old_value} /> : <span aria-hidden="true">—</span>}
          <span className="booking-timeline-transition-arrow" aria-hidden="true">→</span>
          {activity.new_value ? <StatusBadge label={activity.new_value} /> : <span aria-hidden="true">—</span>}
        </div>}
        <ActivityContext activity={activity} />
        <small className="booking-activity-actor">Người thực hiện: {activity.actor.full_name}</small>
      </div>
    </article>)}
    {!activities.length && <p className="empty-state">Chưa có hoạt động.</p>}
  </div>;
}
