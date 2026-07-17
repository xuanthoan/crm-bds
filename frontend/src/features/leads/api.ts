import { apiRequest } from '../../services/apiClient';
import type { AdminUser } from '../admin/users/api';
import type { DuplicateInfo, Lead, LeadActivity, LeadActivityType, LeadPayload, LeadStatus } from './types';

export type LeadFilters = { page?: number; page_size?: number; search?: string; status?: string; priority?: string; source?: string; owner_id?: string; department_id?: string; team_id?: string; created_from?: string; created_to?: string; scope?: string; activity_status?: string; has_activity?: boolean | string; care_status?: string; care_due?: string; next_follow_up?: string; stale?: boolean | string };

export function listLeads(filters: LeadFilters = {}) {
  const params = new URLSearchParams();
  params.set('page', String(filters.page ?? 1));
  params.set('page_size', String(filters.page_size ?? 20));
  Object.entries(filters).forEach(([key, value]) => { if (value !== undefined && value !== '' && key !== 'page' && key !== 'page_size') params.set(key, String(value)); });
  return apiRequest<Lead[]>(`/api/v1/leads?${params.toString()}`);
}
export const getLead = (id: string) => apiRequest<Lead>(`/api/v1/leads/${id}`);
export const createLead = (payload: LeadPayload) => apiRequest<Lead>('/api/v1/leads', { method: 'POST', body: JSON.stringify(payload) });
export const checkLeadDuplicate = (phone: string) => apiRequest<DuplicateInfo>(`/api/v1/leads/duplicate-check?phone=${encodeURIComponent(phone)}`);
export const updateLead = (id: string, payload: LeadPayload) => apiRequest<Lead>(`/api/v1/leads/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
export const changeLeadStatus = (id: string, payload: { status: LeadStatus; lost_reason?: string | null; note?: string | null }) => apiRequest<Lead>(`/api/v1/leads/${id}/status`, { method: 'POST', body: JSON.stringify(payload) });
export const assignLead = (id: string, ownerId: string, note?: string) => apiRequest<Lead>(`/api/v1/leads/${id}/assign`, { method: 'POST', body: JSON.stringify({ owner_id: ownerId, note }) });
export const addLeadActivity = (id: string, payload: { activity_type: LeadActivityType; title?: string; content: string }) => apiRequest<LeadActivity>(`/api/v1/leads/${id}/activities`, { method: 'POST', body: JSON.stringify(payload) });
export const deleteLead = (id: string) => apiRequest<null>(`/api/v1/leads/${id}`, { method: 'DELETE' });
export const listOverdueLeads = (filters: {page?:number;page_size?:number;owner_id?:string;priority?:string;scope?:string;care_status?:string}={}) => { const p=new URLSearchParams();p.set('page',String(filters.page??1));p.set('page_size',String(filters.page_size??20));if(filters.owner_id)p.set('owner_id',filters.owner_id);if(filters.priority)p.set('priority',filters.priority);if(filters.scope)p.set('scope',filters.scope);if(filters.care_status)p.set('care_status',filters.care_status);return apiRequest<Lead[]>(`/api/v1/leads/overdue?${p}`); };
export const transferLead = (id:string,newOwnerId:string,reason:string) => apiRequest<Lead>(`/api/v1/leads/${id}/transfer`,{method:'POST',body:JSON.stringify({new_owner_id:newOwnerId,reason})});
export const reclaimLead = (id:string,newOwnerId:string|undefined,reason:string) => apiRequest<Lead>(`/api/v1/leads/${id}/reclaim`,{method:'POST',body:JSON.stringify({new_owner_id:newOwnerId||null,reason})});

export const listEligibleLeadAssignees = () => apiRequest<AdminUser[]>('/api/v1/organization/lead-scope-users');
