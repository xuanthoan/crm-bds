import { BusinessTimeline } from '../../../components/timeline/BusinessTimeline';
import { ACTIVITY_LABELS, STATUS_LABELS } from '../constants';
import type { LeadActivity } from '../types';

function displayValue(value: string | null) { return value && value in STATUS_LABELS ? STATUS_LABELS[value as keyof typeof STATUS_LABELS] : value; }
function oldTimelineValue(item: LeadActivity) { return item.activity_type === 'assignment' ? item.old_owner_name ?? null : displayValue(item.old_value); }
function newTimelineValue(item: LeadActivity) { return item.activity_type === 'assignment' ? item.new_owner_name ?? null : displayValue(item.new_value); }
export function LeadTimeline({ activities }: { activities: LeadActivity[] }) {
  return <BusinessTimeline emptyText="Chưa có hoạt động lead." items={activities.map(item=>({id:item.id,title:item.title || ACTIVITY_LABELS[item.activity_type] || 'Hoạt động lead',time:new Date(item.created_at).toLocaleString('vi-VN'),actor:item.user.full_name,description:item.content,oldValue:oldTimelineValue(item),newValue:newTimelineValue(item)}))}/>;
}
