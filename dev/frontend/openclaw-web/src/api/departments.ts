import apiClient, { unwrap } from './client';
import type { ApiResponse } from '../types';

interface Department {
  id: string;
  code: string;
  name: string;
  head_user_id?: string;
  is_active: boolean;
}

interface Quota {
  department_id: string;
  max_concurrent_tasks: number;
  max_daily_api_budget?: number;
  max_daily_upload_mb: number;
  max_user_rate: number;
}

interface ModelLock {
  id: string;
  department_id: string;
  task_type: string;
  locked_model: string;
}

export const departmentsApi = {
  list: () => unwrap<Department[]>(apiClient.get<ApiResponse<Department[]>>('/departments')),

  getQuota: (dept_id: string) =>
    unwrap<Quota>(apiClient.get<ApiResponse<Quota>>(`/departments/${dept_id}/quota`)),

  updateQuota: (dept_id: string, data: Partial<Quota>) =>
    unwrap<Quota>(apiClient.put<ApiResponse<Quota>>(`/departments/${dept_id}/quota`, data)),

  getModelLocks: (dept_id: string) =>
    unwrap<ModelLock[]>(apiClient.get<ApiResponse<ModelLock[]>>(`/departments/${dept_id}/model-locks`)),

  setModelLock: (dept_id: string, task_type: string, locked_model: string) =>
    unwrap<ModelLock>(
      apiClient.post<ApiResponse<ModelLock>>(`/departments/${dept_id}/model-locks`, { task_type, locked_model })
    ),

  removeModelLock: (dept_id: string, lock_id: string) =>
    apiClient.delete<ApiResponse<{ deleted: boolean }>>(`/departments/${dept_id}/model-locks/${lock_id}`),
};

export type { Department, Quota, ModelLock };
