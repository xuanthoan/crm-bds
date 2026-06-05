import { STATUS_LABELS } from '../constants';
import type { LeadStatus } from '../types';

export function LeadStatusBadge({ status }: { status: LeadStatus }) {
  const tone = status === 'lost' ? 'red' : status === 'converted' ? 'green' : status === 'new' ? 'blue' : status === 'deposit_ready' ? 'orange' : 'gray';
  return <span className={`badge badge-${tone}`}>{STATUS_LABELS[status]}</span>;
}
