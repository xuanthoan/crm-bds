import { useEffect, useState } from 'react';
import { FormError } from '../../components/FormError';
import { can } from '../auth/authStore';
import type { AdminUser } from '../admin/users/api';
import { navigateTo } from '../../routes/AppRoutes';
import { formatApiError } from '../../services/apiClient';
import { addLeadActivity, changeLeadStatus, getLead, listEligibleLeadAssignees, reclaimLead, transferLead, updateLead } from './api';
import { LEAD_ASSIGN_PERMISSIONS, LEAD_UPDATE_PERMISSIONS, SALES_ROLE_CODES, SOURCE_LABELS } from './constants';
import { LeadActivityForm } from './LeadActivityForm';
import { LeadAssignModal } from './LeadAssignModal';
import { LeadFormModal } from './LeadFormModal';
import { LeadStatusModal } from './LeadStatusModal';
import { LeadPriorityBadge } from './components/LeadPriorityBadge';
import { LeadStatusBadge } from './components/LeadStatusBadge';
import { LeadTimeline } from './components/LeadTimeline';
import type { Lead, LeadPayload } from './types';
import { listTasks, createTask } from '../tasks/api';
import type { LeadTask, TaskPayload } from '../tasks/types';
import { TaskTable } from '../tasks/components/TaskTable';
import { TaskFormModal } from '../tasks/TaskFormModal';
import { listAppointments, createAppointment } from '../appointments/api';
import type { LeadAppointment, AppointmentPayload } from '../appointments/types';
import { AppointmentTable } from '../appointments/components/AppointmentTable';
import { AppointmentFormModal } from '../appointments/AppointmentFormModal';
import { LeadConvertModal } from '../customers/LeadConvertModal';

const hasAny = (permissions: string[]) => permissions.some(can);
const value = (v: unknown) => v === null || v === undefined || v === '' ? '—' : String(v);
const dateTime = (v?: string | null) => v ? new Date(v).toLocaleString('vi-VN') : '—';
const range = (a: unknown, b: unknown, suffix = '') => a || b ? `${value(a)} – ${value(b)}${suffix}` : '—';

export function LeadDetailPage({ leadId }: { leadId: string }) {
  const [lead, setLead] = useState<Lead | null>(null); const [owners, setOwners] = useState<AdminUser[]>([]); const [ownersLoading, setOwnersLoading] = useState(false); const [ownersError, setOwnersError] = useState<string[] | null>(null); const [errors, setErrors] = useState<string[] | null>(null); const [editing, setEditing] = useState(false); const [statusOpen, setStatusOpen] = useState(false); const [assignOpen, setAssignOpen] = useState(false); const [tasks,setTasks]=useState<LeadTask[]>([]); const [appointments,setAppointments]=useState<LeadAppointment[]>([]); const [taskOpen,setTaskOpen]=useState(false); const [appointmentOpen,setAppointmentOpen]=useState(false); const [convertOpen,setConvertOpen]=useState(false);
  const canUpdate = hasAny(LEAD_UPDATE_PERMISSIONS); const canAssign = hasAny(LEAD_ASSIGN_PERMISSIONS);
  async function load() { try { const [leadResponse,taskResponse,appointmentResponse]=await Promise.all([getLead(leadId),listTasks({lead_id:leadId,page_size:10}),listAppointments({lead_id:leadId,page_size:10})]); setLead(leadResponse.data); setTasks(taskResponse.data); setAppointments(appointmentResponse.data); setErrors(null); } catch (error) { setErrors(formatApiError(error, 'Không thể tải chi tiết lead.')); } }
  async function loadEligibleOwners() { setOwnersLoading(true); setOwnersError(null); try { const response = await listEligibleLeadAssignees(); setOwners(response.data.filter((item) => item.roles.some((role) => SALES_ROLE_CODES.includes(role.code)))); } catch (error) { setOwners([]); setOwnersError(formatApiError(error, 'Không thể tải danh sách người phụ trách trong phạm vi được phân công.')); } finally { setOwnersLoading(false); } }
  useEffect(() => { void load(); if (canAssign) void loadEligibleOwners(); }, [leadId]);
  if (!lead) return <section className="admin-page"><button className="secondary-button back-button" onClick={() => navigateTo('/leads')}>← Quay lại</button><FormError messages={errors}/>{!errors && <p>Đang tải…</p>}</section>;
  const info: Array<[string, unknown]> = [['Điện thoại chính', lead.phone_primary], ['Điện thoại phụ', lead.phone_secondary], ['Zalo', lead.zalo], ['Facebook', lead.facebook], ['Email', lead.email], ['Địa chỉ', lead.address], ['Nguồn', lead.source ? SOURCE_LABELS[lead.source] ?? lead.source : null], ['Dự án quan tâm', lead.project_interest], ['Khu vực quan tâm', lead.location_interest], ['Ngân sách', range(lead.budget_min, lead.budget_max, ' đ')], ['Phòng ngủ', lead.bedroom_need], ['Diện tích', range(lead.area_min, lead.area_max, ' m²')], ['Phụ trách', lead.owner?.full_name], ['Người tạo', lead.created_by?.full_name], ['Người phân công', lead.assigned_by?.full_name], ['Liên hệ gần nhất', dateTime(lead.last_contact_at)], ['Chăm sóc tiếp theo', dateTime(lead.next_follow_up_at)], ['Ngày tạo', dateTime(lead.created_at)]];
  async function save(payload: LeadPayload) { await updateLead(leadId, payload); setEditing(false); await load(); }
  return <section className="admin-page lead-detail"><button className="secondary-button back-button" onClick={() => navigateTo('/leads')}>← Quay lại danh sách</button><header className="detail-hero"><div><span className="lead-code">{lead.code}</span><h1>{lead.full_name}</h1><div><LeadStatusBadge status={lead.status}/><LeadPriorityBadge priority={lead.priority}/></div></div><div className="hero-actions">{canUpdate && <><button className="secondary-button" onClick={() => setEditing(true)}>Chỉnh sửa</button><button onClick={() => setStatusOpen(true)}>Đổi trạng thái</button></>}{canAssign && <button onClick={() => { setAssignOpen(true); void loadEligibleOwners(); }}>Chuyển lead</button>}{!lead.converted_customer_id && ['leads.convert.own','leads.convert.team','leads.convert.department','leads.convert.all'].some(can) && <button onClick={() => setConvertOpen(true)}>Chuyển thành khách hàng</button>}{lead.converted_customer && <button className="secondary-button" onClick={() => navigateTo(`/customers/${lead.converted_customer!.id}`)}>Đã chuyển thành khách hàng: {lead.converted_customer.customer_code}</button>}{(can('leads.reclaim.team') || can('leads.reclaim.all')) && <button className="secondary-button" onClick={async () => { const reason = window.prompt('Lý do thu hồi lead', 'Sale không chăm sóc quá hạn'); if (!reason) return; try { await reclaimLead(leadId, undefined, reason); await load(); } catch (error) { setErrors(formatApiError(error)); } }}>Thu hồi</button>}</div></header><FormError messages={errors}/>
    <div className="detail-grid detail-page-grid"><article className="detail-card detail-main"><h2>Thông tin lead</h2><dl className="info-grid">{info.map(([label, content]) => <div key={label}><dt>{label}</dt><dd>{value(content)}</dd></div>)}</dl>{lead.lost_reason && <div className="lost-reason"><strong>Lý do mất khách:</strong> {lead.lost_reason}</div>}<div className="lead-note"><strong>Ghi chú</strong><p>{lead.note || 'Chưa có ghi chú.'}</p></div></article>
      <aside className="detail-card detail-aside detail-activity-card"><h2>Thêm hoạt động</h2>{canUpdate ? <LeadActivityForm onSubmit={async (payload) => { await addLeadActivity(leadId, payload); await load(); }}/> : <p>Bạn không có quyền thêm hoạt động.</p>}</aside></div>
    <article className="detail-card"><header className="section-heading"><h2>Công việc</h2>{can('lead_tasks.create')&&<button onClick={()=>setTaskOpen(true)}>Tạo công việc</button>}</header><div className="responsive-table-wrap"><TaskTable items={tasks} onEdit={()=>navigateTo('/tasks')} onStatus={()=>navigateTo('/tasks')} onDelete={()=>navigateTo('/tasks')}/></div></article>
    <article className="detail-card"><header className="section-heading"><h2>Lịch hẹn</h2>{can('lead_appointments.create')&&<button onClick={()=>setAppointmentOpen(true)}>Tạo lịch hẹn</button>}</header><div className="responsive-table-wrap"><AppointmentTable items={appointments} onEdit={()=>navigateTo('/appointments')} onStatus={()=>navigateTo('/appointments')} onDelete={()=>navigateTo('/appointments')}/></div></article>
    <article className="detail-card"><h2>Dòng thời gian hoạt động</h2><LeadTimeline activities={lead.activities ?? []}/></article>
    {taskOpen&&<TaskFormModal leadId={leadId} ownerId={lead.owner?.id} onClose={()=>setTaskOpen(false)} onSubmit={async(p:TaskPayload)=>{await createTask(p);setTaskOpen(false);await load()}}/>}{appointmentOpen&&<AppointmentFormModal leadId={leadId} ownerId={lead.owner?.id} onClose={()=>setAppointmentOpen(false)} onSubmit={async(p:AppointmentPayload)=>{await createAppointment(p);setAppointmentOpen(false);await load()}}/>}
    {convertOpen && <LeadConvertModal lead={lead} onClose={() => setConvertOpen(false)} onConverted={(customerId) => { setConvertOpen(false); void load(); navigateTo(`/customers/${customerId}`); }}/>}
    {editing && <LeadFormModal lead={lead} owners={owners} canAssign={canAssign} onClose={() => setEditing(false)} onSubmit={save}/>} {statusOpen && <LeadStatusModal lead={lead} onClose={() => setStatusOpen(false)} onSubmit={async (payload) => { await changeLeadStatus(leadId, payload); setStatusOpen(false); await load(); }}/>} {assignOpen && <LeadAssignModal title="Chuyển lead" lead={lead} owners={owners} ownersLoading={ownersLoading} ownersError={ownersError} onRetryOwners={() => void loadEligibleOwners()} onClose={() => setAssignOpen(false)} onSubmit={async (ownerId, note) => { await transferLead(leadId, ownerId, note || 'Chuyển cho sale phù hợp hơn'); setAssignOpen(false); await load(); }}/>}
  </section>;
}
