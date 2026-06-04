import { apiRequest } from '../../../services/apiClient';

export type UserRole = {
  id: string;
  code: string;
  name: string;
};

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  status: 'active' | 'inactive' | 'suspended' | 'resigned';
  roles: UserRole[];
  created_at: string;
  updated_at: string;
};

export type UserListMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type UserPayload = {
  email?: string;
  full_name: string;
  phone?: string | null;
  password?: string;
  status: string;
  role_codes: string[];
};

export function listUsers(filters: { page?: number; page_size?: number; search?: string; status?: string; role_code?: string } = {}) {
  const params = new URLSearchParams();
  params.set('page', String(filters.page ?? 1));
  params.set('page_size', String(filters.page_size ?? 20));
  if (filters.search) params.set('search', filters.search);
  if (filters.status) params.set('status', filters.status);
  if (filters.role_code) params.set('role_code', filters.role_code);
  return apiRequest<AdminUser[]>(`/api/v1/users?${params.toString()}`);
}

export function createUser(payload: UserPayload) {
  return apiRequest<AdminUser>('/api/v1/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateUser(userId: string, payload: UserPayload) {
  return apiRequest<AdminUser>(`/api/v1/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deactivateUser(userId: string) {
  return apiRequest<AdminUser>(`/api/v1/users/${userId}/deactivate`, { method: 'POST' });
}

export function resetUserPassword(userId: string, newPassword: string) {
  return apiRequest<null>(`/api/v1/users/${userId}/reset-password`, {
    method: 'POST',
    body: JSON.stringify({ new_password: newPassword }),
  });
}
