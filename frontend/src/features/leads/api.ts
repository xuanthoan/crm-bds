import { apiRequest } from '../../services/apiClient';
import type { Lead, LeadPayload } from './types';

export function listLeads(filters: Record<string, string | number | undefined> = {}) {
  const params = new URLSearchParams(); Object.entries(filters).forEach(([key, value]) => { if (value !== undefined && value !== '') params.set(key, String(value)); });
  return apiRequest<Lead[]>(`/api/v1/leads?${params.toString()}`);
}
export function getLead(id: string) { return apiRequest<Lead>(`/api/v1/leads/${id}`); }
export function createLead(payload: LeadPayload) { return apiRequest<Lead>('/api/v1/leads', { method: 'POST', body: JSON.stringify(payload) }); }
export function updateLead(id: string, payload: Partial<LeadPayload>) { return apiRequest<Lead>(`/api/v1/leads/${id}`, { method: 'PUT', body: JSON.stringify(payload) }); }
export function changeLeadStatus(id: string, payload: { status: string; lost_reason?: string | null; note?: string | null }) { return apiRequest<Lead>(`/api/v1/leads/${id}/status`, { method: 'POST', body: JSON.stringify(payload) }); }
export function assignLead(id: string, ownerId: string, note?: string) { return apiRequest<Lead>(`/api/v1/leads/${id}/assign`, { method: 'POST', body: JSON.stringify({ owner_id: ownerId, note }) }); }
export function addLeadActivity(id: string, payload: { activity_type: string; title?: string; content: string }) { return apiRequest(`/api/v1/leads/${id}/activities`, { method: 'POST', body: JSON.stringify(payload) }); }
export function deleteLead(id: string) { return apiRequest<null>(`/api/v1/leads/${id}`, { method: 'DELETE' }); }
