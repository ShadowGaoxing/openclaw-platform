import apiClient, { unwrap } from './client';
import type { ApiResponse } from '../types';

interface AgentItem {
  id: string;
  agent_name: string;
  user_id?: string;
  department_id: string;
  version?: string;
  status: 'online' | 'offline' | 'reconnecting' | 'stale' | 'suspected_failure';
  current_concurrency: number;
  max_concurrency: number;
  cpu_pct?: number;
  mem_pct?: number;
  gpu_pct?: number;
  available_models?: string[];
  ip_address?: string;
  last_seen_at?: string;
  registered_at: string;
}

export const agentsApi = {
  list: (params?: { department_id?: string; status_filter?: string }) =>
    unwrap<AgentItem[]>(apiClient.get<ApiResponse<AgentItem[]>>('/agents', { params })),
};

export type { AgentItem };
