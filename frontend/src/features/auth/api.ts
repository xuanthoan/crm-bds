import { apiClient } from '../../services/apiClient';
import type { CurrentUser } from './authStore';

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: CurrentUser;
};

export function login(email: string, password: string) {
  return apiClient<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: { email, password },
  });
}

export function logout(refreshToken: string | null) {
  return apiClient<null>('/api/v1/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  });
}

export function getMe() {
  return apiClient<CurrentUser>('/api/v1/auth/me');
}
