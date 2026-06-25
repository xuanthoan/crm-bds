import { Badge } from '../../../components/Badge';
import { DEAL_PRIORITY_LABELS, DEAL_STATUS_LABELS, PIPELINE_STAGE_LABELS } from '../constants';
import type { DealPriority, DealStage, DealStatus } from '../types';

type BadgeTone = 'green' | 'gray' | 'orange' | 'red' | 'blue';

export const DEAL_STAGE_BADGE_TONES: Record<DealStage, BadgeTone> = {
  new: 'blue',
  consulting: 'blue',
  reserved: 'blue',
  deposited: 'orange',
  deposit: 'orange',
  contract_pending: 'orange',
  contract: 'orange',
  contract_signed: 'green',
  completed: 'green',
  lost: 'red',
  viewing: 'blue',
  negotiating: 'orange',
};

export const DEAL_STATUS_BADGE_TONES: Record<DealStatus, BadgeTone> = {
  open: 'blue',
  pending: 'orange',
  negotiating: 'orange',
  contract_pending: 'orange',
  payment_pending: 'orange',
  payment: 'orange',
  payment_in_progress: 'orange',
  signed: 'green',
  contracted: 'green',
  active: 'green',
  completed: 'green',
  won: 'green',
  lost: 'red',
  cancelled: 'red',
};

export const DEAL_PRIORITY_BADGE_TONES: Record<DealPriority, BadgeTone> = {
  low: 'gray',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
};

export function DealBadge({ stage, status, priority }: { stage?: DealStage; status?: DealStatus; priority?: DealPriority }) {
  if (stage) return <Badge tone={DEAL_STAGE_BADGE_TONES[stage]}>{PIPELINE_STAGE_LABELS[stage]}</Badge>;
  if (status) return <Badge tone={DEAL_STATUS_BADGE_TONES[status]}>{DEAL_STATUS_LABELS[status]}</Badge>;
  if (priority) return <Badge tone={DEAL_PRIORITY_BADGE_TONES[priority]}>{DEAL_PRIORITY_LABELS[priority]}</Badge>;
  return <Badge tone="gray">—</Badge>;
}
