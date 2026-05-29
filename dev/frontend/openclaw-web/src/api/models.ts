import apiClient, { unwrap } from './client';
import type { ApiResponse, ModelOption } from '../types';

interface ModelRegistryItem {
  id: string;
  model_name: string;
  model_type: 'local' | 'api';
  deploy_location?: string;
  supported_task_types: string[];
  cost_per_call: number;
  avg_latency_ms?: number;
  status: 'online' | 'offline' | 'degraded';
  max_pool_size?: number;
  min_ram_gb?: number;
  version?: string;
}

export const modelsApi = {
  list: (params?: { task_type?: string; status_filter?: string }) =>
    unwrap<ModelRegistryItem[]>(
      apiClient.get<ApiResponse<ModelRegistryItem[]>>('/models', { params })
    ),

  create: (data: Partial<ModelRegistryItem>) =>
    unwrap<ModelRegistryItem>(
      apiClient.post<ApiResponse<ModelRegistryItem>>('/models', data)
    ),

  update: (id: string, data: Partial<ModelRegistryItem>) =>
    unwrap<ModelRegistryItem>(
      apiClient.put<ApiResponse<ModelRegistryItem>>(`/models/${id}`, data)
    ),
};

/** 把后端模型转成前端展示用 ModelOption */
export function modelToOption(m: ModelRegistryItem, installed = false, locked = false): ModelOption {
  return {
    id: m.id,
    name: m.model_name,
    model_type: m.model_type,
    cost_per_call: m.cost_per_call,
    avg_latency_ms: m.avg_latency_ms || 0,
    is_installed: m.model_type === 'api' || installed,
    is_locked: locked,
    deploy_location: m.deploy_location || '',
  };
}
