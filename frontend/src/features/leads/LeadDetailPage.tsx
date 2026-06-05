import { useEffect, useState } from 'react';
import { FormError } from '../../components/FormError';
import { can } from '../auth/authStore';
import { listUsers, type AdminUser } from '../admin/users/api';
import { navigateTo } from '../../routes/AppRoutes';
import { formatApiError } from '../../services/apiClient';
import { addLeadActivity, assignLead, changeLeadStatus, getLead, updateLead } from './api';
import { LEAD_ASSIGN_PERMISSIONS, LEAD_UPDATE_PERMISSIONS, SALES_ROLE_CODES, SOURCE_LABELS } from './constants';
import { LeadActivityForm } from './LeadActivityForm';
import { LeadAssignModal } from './LeadAssignModal';
import { LeadFormModal } from './LeadFormModal';
import { LeadStatusModal } from './LeadStatusModal';
import { LeadPriorityBadge } from './components/LeadPriorityBadge';
import { LeadStatusBadge } from './components/LeadStatusBadge';
import { LeadTimeline } from './components/LeadTimeline';
import type { Lead, LeadPayload } from './types';

const hasAny = (permissions: string[]) => permissions.some(can);
const value = (v: unknown) => v === null || v === undefined || v === '' ? '—' : String(v);
const dateTime = (v?: string | null) => v ? new Date(v).toLocaleString('vi-VN') : '—';
const range = (a: unknown, b: unknown, suffix = '') => a || b ? `${value(a)} – ${value(b)}${suffix}` : '—';

export function LeadDetailPage({ leadId }: { leadId: string }) {
  const [lead, setLead] = useState<Lead | null>(null); const [owners, setOwners] = useState<AdminUser[]>([]); const [errors, setErrors] = useState<string[] | null>(null); const [editing, setEditing] = useState(false); const [statusOpen, setStatusOpen] = useState(false); const [assignOpen, setAssignOpen] = useState(false);
  const canUpdate = hasAny(LEAD_UPDATE_PERMISSIONS); const canAssign = hasAny(LEAD_ASSIGN_PERMISSIONS);
  async function load() { try { setLead((await getLead(leadId)).data); setErrors(null); } catch (error) { setErrors(formatApiError(error, 'Không thể tải chi tiết lead.')); } }
  useEffect(() => { void load(); if (can('users.view')) void listUsers({ page_size: 100, status: 'active' }).then((r) => setOwners(r.data.filter((u) => u.roles.some((role) => SALES_ROLE_CODES.includes(role.code))))).catch(() => setOwners([])); }, [leadId]);
  if (!lead) return <section className="admin-page"><button className="secondary-button back-button" onClick={() => navigateTo('/leads')}>← Quay lại</button><FormError messages={errors}/>{!errors && <p>Đang tải…</p>}</section>;
  const info: Array<[string, unknown]> = [['Điện thoại chính', lead.phone_primary], ['Điện thoại phụ', lead.phone_secondary], ['Zalo', lead.zalo], ['Facebook', lead.facebook], ['Email', lead.email], ['Địa chỉ', lead.address], ['Nguồn', lead.source ? SOURCE_LABELS[lead.source] ?? lead.source : null], ['Dự án quan tâm', lead.project_interest], ['Khu vực quan tâm', lead.location_interest], ['Ngân sách', range(lead.budget_min, lead.budget_max, ' đ')], ['Phòng ngủ', lead.bedroom_need], ['Diện tích', range(lead.area_min, lead.area_max, ' m²')], ['Phụ trách', lead.owner?.full_name], ['Người tạo', lead.created_by?.full_name], ['Người phân công', lead.assigned_by?.full_name], ['Liên hệ gần nhất', dateTime(lead.last_contact_at)], ['Chăm sóc tiếp theo', dateTime(lead.next_follow_up_at)], ['Ngày tạo', dateTime(lead.created_at)]];
  async function save(payload: LeadPayload) { await updateLead(leadId, payload); setEditing(false); await load(); }
  return <section className="admin-page lead-detail"><button className="secondary-button back-button" onClick={() => navigateTo('/leads')}>← Quay lại danh sách</button><header className="detail-hero"><div><span className="lead-code">{lead.code}</span><h1>{lead.full_name}</h1><div><LeadStatusBadge status={lead.status}/><LeadPriorityBadge priority={lead.priority}/></div></div><div className="hero-actions">{canUpdate && <><button className="secondary-button" onClick={() => setEditing(true)}>Chỉnh sửa</button><button onClick={() => setStatusOpen(true)}>Đổi trạng thái</button></>}{canAssign && <button onClick={() => setAssignOpen(true)}>Phân công</button>}</div></header><FormError messages={errors}/>
    <div className="detail-grid"><article className="detail-card"><h2>Thông tin lead</h2><dl className="info-grid">{info.map(([label, content]) => <div key={label}><dt>{label}</dt><dd>{value(content)}</dd></div>)}</dl>{lead.lost_reason && <div className="lost-reason"><strong>Lý do mất khách:</strong> {lead.lost_reason}</div>}<div className="lead-note"><strong>Ghi chú</strong><p>{lead.note || 'Chưa có ghi chú.'}</p></div></article>
      <aside className="detail-card"><h2>Thêm hoạt động</h2>{canUpdate ? <LeadActivityForm onSubmit={async (payload) => { await addLeadActivity(leadId, payload); await load(); }}/> : <p>Bạn không có quyền thêm hoạt động.</p>}</aside></div>
    <article className="detail-card"><h2>Dòng thời gian</h2><LeadTimeline activities={lead.activities ?? []}/></article>
    {editing && <LeadFormModal lead={lead} owners={owners} canAssign={canAssign} onClose={() => setEditing(false)} onSubmit={save}/>} {statusOpen && <LeadStatusModal lead={lead} onClose={() => setStatusOpen(false)} onSubmit={async (payload) => { await changeLeadStatus(leadId, payload); setStatusOpen(false); await load(); }}/>} {assignOpen && <LeadAssignModal lead={lead} owners={owners} onClose={() => setAssignOpen(false)} onSubmit={async (ownerId, note) => { await assignLead(leadId, ownerId, note); setAssignOpen(false); await load(); }}/>}
  </section>;
}
