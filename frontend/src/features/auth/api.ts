import { apiRequest } from '../../services/apiClient';

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  status: string;
  roles: string[];
  permissions: string[];
  is_superuser: boolean;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  user: AuthUser;
};

export function login(email: string, password: string) {
  return apiRequest<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function logout(refreshToken: string | null) {
  return apiRequest<null>('/api/v1/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function getMe() {
  return apiRequest<AuthUser>('/api/v1/auth/me');
}
