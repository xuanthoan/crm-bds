import { apiRequest } from '../../../services/apiClient';

export type PermissionItem = {
  id: string;
  code: string;
  name: string;
  module: string;
  description: string | null;
};

export type PermissionGroup = {
  module: string;
  permissions: PermissionItem[];
};

export function listPermissions(filters: { module?: string; search?: string } = {}) {
  const params = new URLSearchParams();
  if (filters.module) params.set('module', filters.module);
  if (filters.search) params.set('search', filters.search);
  const query = params.toString();
  return apiRequest<PermissionGroup[]>(`/api/v1/permissions${query ? `?${query}` : ''}`);
}
