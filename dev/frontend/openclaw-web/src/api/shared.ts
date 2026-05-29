import apiClient, { unwrap } from './client';
import type { ApiResponse, SharedResult } from '../types';

export const sharedApi = {
  list: (params?: { status_filter?: string; source_dept?: string }) =>
    unwrap<SharedResult[]>(
      apiClient.get<ApiResponse<SharedResult[]>>('/shared', { params })
    ),

  pendingApprovals: () =>
    unwrap<SharedResult[]>(
      apiClient.get<ApiResponse<SharedResult[]>>('/shared/pending-approvals')
    ),

  share: (data: {
    task_id: string;
    target_department_id?: string;
    target_user_id?: string;
    file_url: string;
    file_hash?: string;
    output_format?: string;
  }) =>
    unwrap<SharedResult>(
      apiClient.post<ApiResponse<SharedResult>>('/shared', data)
    ),

  approve: (id: string, action: 'approved' | 'rejected') =>
    unwrap<SharedResult>(
      apiClient.post<ApiResponse<SharedResult>>(`/shared/${id}/approve`, { action })
    ),
};
