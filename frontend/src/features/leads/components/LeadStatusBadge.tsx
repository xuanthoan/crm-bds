import { Badge } from '../../../components/Badge';
import { LEAD_STATUSES } from '../constants';
export function LeadStatusBadge({ status }: { status: string }) { return <Badge tone={status === 'lost' ? 'red' : status === 'converted' ? 'green' : status === 'new' ? 'blue' : 'orange'}>{LEAD_STATUSES[status] ?? status}</Badge>; }
