import { BusinessTimeline } from '../../../components/timeline/BusinessTimeline';
import type { BookingActivity, BookingActivityContext } from '../types';

const money = (value: string) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(value));
const statusTitles: Record<string,string> = {'Mới tạo':'Tạo booking','Đã giữ chỗ':'Giữ chỗ','Đã cọc':'Đặt cọc','Đã hủy':'Hủy booking','Hết hạn giữ chỗ':'Hết hạn giữ chỗ','Đã hoàn tiền':'Hoàn tiền'};
const contextLabels: Array<[keyof BookingActivityContext, string, boolean]> = [['booking_amount','Tiền giữ chỗ',true],['deposit_amount','Tiền cọc',true],['refund_amount','Số tiền hoàn',true],['deduction_amount','Khấu trừ',true],['cancel_reason','Lý do hủy',false],['refund_reason','Lý do hoàn tiền',false],['deduction_reason','Lý do khấu trừ',false],['note','Ghi chú',false]];
function activityTitle(activity: BookingActivity) { return (activity.new_value && statusTitles[activity.new_value]) || activity.title || activity.activity_label || 'Hoạt động booking'; }
function meta(activity: BookingActivity){const entries=contextLabels.filter(([key])=>activity.context?.[key]); if(!entries.length) return null; return <dl className="business-timeline-details">{entries.map(([key,label,isMoney])=>{const value=activity.context[key]!; return <div key={key}><dt>{label}</dt><dd>{isMoney?money(value):value}</dd></div>;})}</dl>;}
export function BookingTimeline({ activities }: { activities: BookingActivity[] }) {
  return <BusinessTimeline emptyText="Chưa có hoạt động booking." items={activities.map(activity=>({id:activity.id,title:activityTitle(activity),time:new Date(activity.created_at).toLocaleString('vi-VN'),actor:activity.actor.full_name,description:activity.content,oldValue:activity.old_value,newValue:activity.new_value,meta:meta(activity)}))}/>;
}
