import { PAYMENT_STATUS_LABELS, PAYMENT_STATUS_TONES } from './constants';
export function PaymentBadge({ status }: { status: string }) { return <span className={`badge ${PAYMENT_STATUS_TONES[status] || 'neutral'}`}>{PAYMENT_STATUS_LABELS[status] || 'Không xác định'}</span>; }
