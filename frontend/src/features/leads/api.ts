import { apiRequest } from '../../services/apiClient';
import type { Lead, LeadActivity, LeadActivityType, LeadPayload, LeadStatus } from './types';

export type LeadFilters = { page?: number; page_size?: number; search?: string; status?: string; priority?: string; source?: string; owner_id?: string; created_from?: string; created_to?: string };

export function listLeads(filters: LeadFilters = {}) {
  const params = new URLSearchParams();
  params.set('page', String(filters.page ?? 1));
  params.set('page_size', String(filters.page_size ?? 20));
  Object.entries(filters).forEach(([key, value]) => { if (value !== undefined && value !== '' && key !== 'page' && key !== 'page_size') params.set(key, String(value)); });
  return apiRequest<Lead[]>(`/api/v1/leads?${params.toString()}`);
}
export const getLead = (id: string) => apiRequest<Lead>(`/api/v1/leads/${id}`);
export const createLead = (payload: LeadPayload) => apiRequest<Lead>('/api/v1/leads', { method: 'POST', body: JSON.stringify(payload) });
export const updateLead = (id: string, payload: LeadPayload) => apiRequest<Lead>(`/api/v1/leads/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
export const changeLeadStatus = (id: string, payload: { status: LeadStatus; lost_reason?: string | null; note?: string | null }) => apiRequest<Lead>(`/api/v1/leads/${id}/status`, { method: 'POST', body: JSON.stringify(payload) });
export const assignLead = (id: string, ownerId: string, note?: string) => apiRequest<Lead>(`/api/v1/leads/${id}/assign`, { method: 'POST', body: JSON.stringify({ owner_id: ownerId, note }) });
export const addLeadActivity = (id: string, payload: { activity_type: LeadActivityType; title?: string; content: string }) => apiRequest<LeadActivity>(`/api/v1/leads/${id}/activities`, { method: 'POST', body: JSON.stringify(payload) });
export const deleteLead = (id: string) => apiRequest<null>(`/api/v1/leads/${id}`, { method: 'DELETE' });
