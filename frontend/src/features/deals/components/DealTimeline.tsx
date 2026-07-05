import { BusinessTimeline } from '../../../components/timeline/BusinessTimeline';
import { ACTIVITY_LABELS } from '../constants';
import type { DealActivity } from '../types';

const fmt=(v:string)=>new Date(v).toLocaleString('vi-VN');
function title(a:DealActivity){return a.title || ACTIVITY_LABELS[a.activity_type as keyof typeof ACTIVITY_LABELS] || a.activity_type || 'Hoạt động giao dịch';}
export function DealTimeline({ activities = [] }: { activities?: DealActivity[] }) {
  return <BusinessTimeline emptyText="Chưa có hoạt động giao dịch." items={activities.map(a=>({
    id:a.id,
    title:title(a),
    time:fmt(a.created_at),
    actor:a.user?.full_name || 'Người dùng hệ thống',
    description:a.content || (ACTIVITY_LABELS[a.activity_type as keyof typeof ACTIVITY_LABELS] || ''),
    oldValue:a.old_value,
    newValue:a.new_value,
  }))}/>;
}
