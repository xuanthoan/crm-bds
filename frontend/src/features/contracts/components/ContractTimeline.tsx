import type { ContractActivity } from '../types';

const formatVnd = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return 'Chưa cập nhật';
  const amount = Number(value);
  if (!Number.isFinite(amount)) return 'Chưa cập nhật';
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(amount)} đ`;
};

const show = (value: string | null | undefined) => value || 'Chưa cập nhật';

const formatTime = (value: string) =>
  new Intl.DateTimeFormat('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: 'numeric',
    month: 'numeric',
    year: 'numeric',
  }).format(new Date(value));

function toneForContractTimelineValue(value?: string | null) {
  const text = (value || '').toLowerCase();
  if (!text) return 'muted';
  if (/(hủy|huỷ|cancelled)/i.test(value || '')) return 'danger';
  if (/(đã ký|có hiệu lực|hoàn tất|đã thanh toán|signed|active|completed|paid)/i.test(value || '')) return 'success';
  if (/(chờ|dự kiến|quá hạn|pending|planned|overdue|due)/i.test(value || '')) return 'info';
  if (/(bản nháp|mới tạo|draft|new)/i.test(value || '')) return 'draft';
  return 'muted';
}

function ContractTimelineValueBadge({ value }: { value?: string | null }) {
  return <span className={`contract-timeline-value-badge contract-timeline-value-badge--${toneForContractTimelineValue(value)}`}>{value || '—'}</span>;
}

function PaymentDetails({ activity }: { activity: ContractActivity }) {
  const metadata = activity.metadata ?? {};
  if (activity.activity_type === 'payment_created') {
    return (
      <dl className="contract-timeline-details">
        <div><dt>Số tiền</dt><dd>{formatVnd(metadata.amount)}</dd></div>
        <div><dt>Loại thanh toán</dt><dd>{show(metadata.payment_type_label)}</dd></div>
        <div><dt>Trạng thái</dt><dd>{show(metadata.payment_status_label)}</dd></div>
      </dl>
    );
  }
  if (activity.activity_type === 'payment_paid') {
    return (
      <dl className="contract-timeline-details">
        <div><dt>Số tiền</dt><dd>{formatVnd(metadata.amount)}</dd></div>
        <div><dt>Phương thức</dt><dd>{show(metadata.payment_method_label)}</dd></div>
        <div><dt>Mã tham chiếu</dt><dd>{show(metadata.reference_number)}</dd></div>
        <div><dt>Ngày thanh toán</dt><dd>{metadata.paid_date ? formatTime(metadata.paid_date) : 'Chưa cập nhật'}</dd></div>
      </dl>
    );
  }
  return null;
}

export function ContractTimeline({ items }: { items: ContractActivity[] }) {
  return (
    <div className="lead-timeline contract-timeline">
      {items.map((activity) => (
        <article className="timeline-item" key={activity.id}>
          <span className="timeline-marker" />
          <div>
            <header>
              <strong>{activity.activity_label}</strong>
              <time>{formatTime(activity.created_at)}</time>
            </header>
            <h4>{activity.title}</h4>
            {activity.old_value && activity.new_value && (
              <span className="value-change contract-timeline-transition"><ContractTimelineValueBadge value={activity.old_value}/><span className="contract-timeline-transition-arrow">→</span><ContractTimelineValueBadge value={activity.new_value}/></span>
            )}
            <PaymentDetails activity={activity} />
            {activity.content && <p className="contract-timeline-note">Ghi chú: {activity.content}</p>}
            <small>Người thực hiện: {activity.actor.full_name}</small>
            <small>Thời gian: {formatTime(activity.created_at)}</small>
          </div>
        </article>
      ))}
      {!items.length && <p className="empty-state">Chưa có hoạt động.</p>}
    </div>
  );
}
