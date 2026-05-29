import apiClient, { unwrap } from './client';
import type { ApiResponse } from '../types';

interface DashboardStats {
  total_tasks: number;
  pending_tasks: number;
  processing_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  dead_tasks: number;
  online_agents: number;
  offline_agents: number;
  suspected_agents: number;
  today_completed: number;
}

interface AuditLogItem {
  id: number;
  actor_id: string;
  actor_role: string;
  action_type: string;
  target_type: string;
  target_id: string;
  old_value?: Record<string, unknown>;
  new_value?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

export const adminApi = {
  getStats: (department_id?: string) =>
    unwrap<DashboardStats>(
      apiClient.get<ApiResponse<DashboardStats>>('/admin/stats', { params: { department_id } })
    ),

  getAuditLogs: (params?: { action_type?: string; target_type?: string; page?: number; page_size?: number }) =>
    unwrap<AuditLogItem[]>(
      apiClient.get<ApiResponse<AuditLogItem[]>>('/admin/audit-logs', { params })
    ),
};

export type { DashboardStats, AuditLogItem };
