import { apiRequest } from '../../../services/apiClient';

export type RoleSummary = {
  id: string;
  name: string;
  code: string;
  description: string | null;
  is_system: boolean;
  permission_count: number;
  created_at: string;
  updated_at: string;
};

export type RoleDetail = RoleSummary & {
  permission_codes: string[];
  permissions: { module: string; permission_codes: string[] }[];
};

export type RolePayload = {
  name: string;
  code?: string;
  description?: string | null;
  permission_codes?: string[];
};

export function listRoles() {
  return apiRequest<RoleSummary[]>('/api/v1/roles');
}

export function getRole(roleId: string) {
  return apiRequest<RoleDetail>(`/api/v1/roles/${roleId}`);
}

export function createRole(payload: Required<Pick<RolePayload, 'name' | 'code'>> & RolePayload) {
  return apiRequest<RoleDetail>('/api/v1/roles', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateRole(roleId: string, payload: RolePayload) {
  return apiRequest<RoleDetail>(`/api/v1/roles/${roleId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function assignRolePermissions(roleId: string, permissionCodes: string[]) {
  return apiRequest<RoleDetail>(`/api/v1/roles/${roleId}/permissions`, {
    method: 'POST',
    body: JSON.stringify({ permission_codes: permissionCodes }),
  });
}
