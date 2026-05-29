import apiClient, { unwrap } from './client';
import type { ApiResponse, PaginatedResponse, Task } from '../types';

interface TaskListParams {
  status?: string;
  department_id?: string;
  assignee_id?: string;
  mine?: boolean;
  page?: number;
  page_size?: number;
}

interface CreateTaskParams {
  title: string;
  description?: string;
  department_id: string;
  priority?: number;
  assignment_strategy?: 'manual' | 'auto' | 'hybrid';
  recommended_model?: string;
}

interface ClaimResponse {
  task_id: string;
  claimed_at: string;
  claim_timeout_at: string;
}

interface SubmitParams {
  result_url: string;
  file_hash: string;
  output_format?: string;
  override_model_used?: string;
}

export const tasksApi = {
  list: (params: TaskListParams = {}) =>
    unwrap<PaginatedResponse<Task>>(
      apiClient.get<ApiResponse<PaginatedResponse<Task>>>('/tasks', { params })
    ),

  get: (id: string) =>
    unwrap<Task>(apiClient.get<ApiResponse<Task>>(`/tasks/${id}`)),

  create: (data: CreateTaskParams) =>
    unwrap<Task>(apiClient.post<ApiResponse<Task>>('/tasks', data)),

  claim: (id: string, user_id?: string) =>
    unwrap<ClaimResponse>(
      apiClient.post<ApiResponse<ClaimResponse>>(`/tasks/${id}/claim`, { user_id })
    ),

  start: (id: string) =>
    unwrap<{ task_id: string; started_at: string }>(
      apiClient.post<ApiResponse<{ task_id: string; started_at: string }>>(`/tasks/${id}/start`)
    ),

  reportProgress: (id: string, progress_seq: number, progress_pct: number, status_message = '') =>
    unwrap<{ received_seq: number; progress_pct: number }>(
      apiClient.post<ApiResponse<{ received_seq: number; progress_pct: number }>>(
        `/tasks/${id}/progress`,
        { progress_seq, progress_pct, status_message }
      )
    ),

  submit: (id: string, data: SubmitParams) =>
    unwrap<{ task_id: string; file_integrity_verified: boolean; completed_at?: string }>(
      apiClient.post<ApiResponse<{ task_id: string; file_integrity_verified: boolean; completed_at?: string }>>(
        `/tasks/${id}/submit`,
        data
      )
    ),

  release: (id: string) =>
    unwrap<{ task_id: string; status: string }>(
      apiClient.post<ApiResponse<{ task_id: string; status: string }>>(`/tasks/${id}/release`)
    ),

  overrideModel: (id: string, override_model: string) =>
    unwrap<{ task_id: string; override_model: string }>(
      apiClient.post<ApiResponse<{ task_id: string; override_model: string }>>(
        `/tasks/${id}/override-model`,
        { override_model }
      )
    ),
};
