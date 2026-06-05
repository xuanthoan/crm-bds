import { Badge } from '../../../components/Badge';
import { LEAD_PRIORITIES } from '../constants';
export function LeadPriorityBadge({ priority }: { priority: string }) { return <Badge tone={priority === 'urgent' ? 'red' : priority === 'high' ? 'orange' : priority === 'medium' ? 'blue' : 'gray'}>{LEAD_PRIORITIES[priority] ?? priority}</Badge>; }
