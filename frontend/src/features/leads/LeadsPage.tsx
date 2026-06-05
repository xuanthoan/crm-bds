import { useEffect, useState } from 'react';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { FormError } from '../../components/FormError';
import { can } from '../auth/authStore';
import { listUsers, type AdminUser } from '../admin/users/api';
import { formatApiError } from '../../services/apiClient';
import { navigateTo } from '../../routes/AppRoutes';
import { assignLead, changeLeadStatus, createLead, deleteLead, listLeads, updateLead, type LeadFilters as Filters } from './api';
import { LEAD_ASSIGN_PERMISSIONS, LEAD_UPDATE_PERMISSIONS, SALES_ROLE_CODES, SOURCE_LABELS } from './constants';
import { LeadAssignModal } from './LeadAssignModal';
import { LeadFormModal } from './LeadFormModal';
import { LeadStatusModal } from './LeadStatusModal';
import { LeadFilters } from './components/LeadFilters';
import { LeadPriorityBadge } from './components/LeadPriorityBadge';
import { LeadStatusBadge } from './components/LeadStatusBadge';
import type { Lead, LeadPayload } from './types';

const hasAny = (permissions: string[]) => permissions.some(can);
const money = (min: Lead['budget_min'], max: Lead['budget_max']) => !min && !max ? '—' : `${min ? Number(min).toLocaleString('vi-VN') : '0'} – ${max ? Number(max).toLocaleString('vi-VN') : '∞'}`;
const dateTime = (value: string | null) => value ? new Date(value).toLocaleString('vi-VN') : '—';

export function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]); const [owners, setOwners] = useState<AdminUser[]>([]); const [filters, setFilters] = useState<Filters>({ page: 1, page_size: 20 }); const [meta, setMeta] = useState({ page: 1, total_pages: 0, total: 0 }); const [loading, setLoading] = useState(true); const [errors, setErrors] = useState<string[] | null>(null);
  const [editing, setEditing] = useState<Lead | null | undefined>(undefined); const [statusLead, setStatusLead] = useState<Lead | null>(null); const [assigning, setAssigning] = useState<Lead | null>(null); const [deleting, setDeleting] = useState<Lead | null>(null);
  const canUpdate = hasAny(LEAD_UPDATE_PERMISSIONS); const canAssign = hasAny(LEAD_ASSIGN_PERMISSIONS);
  async function load(next = filters) { setLoading(true); setErrors(null); try { const response = await listLeads(next); setLeads(response.data); setMeta(response.meta as typeof meta); } catch (error) { setErrors(formatApiError(error, 'Không thể tải danh sách lead.')); } finally { setLoading(false); } }
  useEffect(() => { void load(); if (can('users.view')) void listUsers({ page_size: 100, status: 'active' }).then((r) => setOwners(r.data.filter((u) => u.roles.some((role) => SALES_ROLE_CODES.includes(role.code))))).catch(() => setOwners([])); }, []);
  async function save(payload: LeadPayload) { if (editing) await updateLead(editing.id, payload); else await createLead(payload); setEditing(undefined); await load(); }
  async function remove() { if (!deleting) return; try { await deleteLead(deleting.id); setDeleting(null); await load(); } catch (error) { setErrors(formatApiError(error)); setDeleting(null); } }
  return <section className="admin-page leads-page"><header className="page-header"><div><h1>Khách tiềm năng</h1><p>Quản lý và chăm sóc lead bất động sản theo phạm vi được phân quyền.</p></div>{can('leads.create') && <button onClick={() => setEditing(null)}>Tạo lead</button>}</header>
    <LeadFilters filters={filters} owners={owners} onChange={setFilters} onSearch={() => { const next = { ...filters, page: 1 }; setFilters(next); void load(next); }} /><FormError messages={errors}/>
    <div className="table-card"><table><thead><tr><th>Mã</th><th>Khách hàng</th><th>Nguồn / dự án</th><th>Ngân sách</th><th>Trạng thái</th><th>Ưu tiên</th><th>Phụ trách</th><th>Chăm sóc tiếp</th><th>Ngày tạo</th><th>Thao tác</th></tr></thead><tbody>
      {loading ? <tr><td colSpan={10}>Đang tải…</td></tr> : leads.length === 0 ? <tr><td colSpan={10}>Chưa có lead phù hợp.</td></tr> : leads.map((lead) => <tr key={lead.id}><td><button className="link-button" onClick={() => navigateTo(`/leads/${lead.id}`)}>{lead.code}</button></td><td><strong>{lead.full_name}</strong><small className="cell-subtitle">{lead.phone_primary}{lead.phone_secondary ? ` · ${lead.phone_secondary}` : ''}</small></td><td>{lead.source ? SOURCE_LABELS[lead.source] ?? lead.source : '—'}<small className="cell-subtitle">{lead.project_interest ?? 'Chưa có dự án'}</small></td><td>{money(lead.budget_min, lead.budget_max)}</td><td><LeadStatusBadge status={lead.status}/></td><td><LeadPriorityBadge priority={lead.priority}/></td><td>{lead.owner?.full_name ?? 'Chưa phân công'}</td><td>{dateTime(lead.next_follow_up_at)}</td><td>{dateTime(lead.created_at)}</td><td><div className="action-cell"><button className="link-button" onClick={() => navigateTo(`/leads/${lead.id}`)}>Chi tiết</button>{canUpdate && <><button className="link-button" onClick={() => setEditing(lead)}>Sửa</button><button className="link-button" onClick={() => setStatusLead(lead)}>Trạng thái</button></>}{canAssign && <button className="link-button" onClick={() => setAssigning(lead)}>Phân công</button>}{can('leads.delete') && <button className="link-button danger-link" onClick={() => setDeleting(lead)}>Xóa</button>}</div></td></tr>)}
    </tbody></table></div>
    <footer className="pagination-row"><span>Tổng {meta.total} lead</span><div><button className="secondary-button" disabled={meta.page <= 1} onClick={() => { const next = { ...filters, page: meta.page - 1 }; setFilters(next); void load(next); }}>Trước</button><span className="page-number">Trang {meta.page}/{Math.max(meta.total_pages, 1)}</span><button className="secondary-button" disabled={meta.page >= meta.total_pages} onClick={() => { const next = { ...filters, page: meta.page + 1 }; setFilters(next); void load(next); }}>Sau</button></div></footer>
    {editing !== undefined && <LeadFormModal lead={editing} owners={owners} canAssign={canAssign} onClose={() => setEditing(undefined)} onSubmit={save}/>} {statusLead && <LeadStatusModal lead={statusLead} onClose={() => setStatusLead(null)} onSubmit={async (payload) => { await changeLeadStatus(statusLead.id, payload); setStatusLead(null); await load(); }}/>} {assigning && <LeadAssignModal lead={assigning} owners={owners} onClose={() => setAssigning(null)} onSubmit={async (ownerId, note) => { await assignLead(assigning.id, ownerId, note); setAssigning(null); await load(); }}/>} {deleting && <ConfirmDialog title="Xóa lead" message={`Lead ${deleting.code} sẽ được xóa mềm và không còn xuất hiện trong danh sách.`} confirmLabel="Xóa lead" onCancel={() => setDeleting(null)} onConfirm={() => void remove()}/>}
  </section>;
}
