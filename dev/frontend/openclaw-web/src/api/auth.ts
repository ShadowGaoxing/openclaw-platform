import apiClient, { unwrap } from './client';
import type { ApiResponse, User } from '../types';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: User;
}

export const authApi = {
  login: (data: LoginRequest) =>
    unwrap<LoginResponse>(apiClient.post<ApiResponse<LoginResponse>>('/auth/login', data)),

  register: (data: { username: string; password: string; display_name: string; department_id: string; role?: string; email?: string }) =>
    unwrap<LoginResponse>(apiClient.post<ApiResponse<LoginResponse>>('/auth/register', data)),

  logout: () =>
    apiClient.post('/auth/logout').catch(() => undefined),

  getProfile: () =>
    unwrap<User>(apiClient.get<ApiResponse<User>>('/auth/profile')),
};
