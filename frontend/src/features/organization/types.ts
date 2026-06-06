import type { AdminUser } from '../admin/users/api';
export type OrganizationUser = Pick<AdminUser, 'id' | 'full_name' | 'email' | 'roles'>;
export type Department = { id: string; code: string; name: string; description: string | null; manager: OrganizationUser | null; status: 'active'|'inactive'; team_count: number; member_count: number; created_at: string; updated_at: string };
export type Team = { id: string; code: string; name: string; description: string | null; department: Pick<Department,'id'|'code'|'name'>; leader: OrganizationUser | null; status: 'active'|'inactive'; member_count: number; created_at: string; updated_at: string };
export type Membership = { id: string; user: OrganizationUser; department: Pick<Department,'id'|'code'|'name'>; team: (Pick<Team,'id'|'code'|'name'> & {department_id:string}) | null; is_primary: boolean; position_title: string | null; created_at: string; updated_at: string };
export type DepartmentPayload = { code?: string; name: string; description?: string | null; manager_id?: string | null; status: string };
export type TeamPayload = { department_id: string; code?: string; name: string; description?: string | null; leader_id?: string | null; status: string };
export type MembershipPayload = { user_id?: string; department_id?: string | null; team_id?: string | null; position_title?: string | null; is_primary: boolean };
