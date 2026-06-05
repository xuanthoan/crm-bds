import { PRIORITY_LABELS } from '../constants';
import type { LeadPriority } from '../types';

export function LeadPriorityBadge({ priority }: { priority: LeadPriority }) {
  const tone = priority === 'urgent' ? 'red' : priority === 'high' ? 'orange' : priority === 'medium' ? 'blue' : 'gray';
  return <span className={`badge badge-${tone}`}>{PRIORITY_LABELS[priority]}</span>;
}
