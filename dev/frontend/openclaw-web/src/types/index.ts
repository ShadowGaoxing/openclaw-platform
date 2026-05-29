// ========== 用户与认证 ==========
export type UserRole = 'admin' | 'dept_head' | 'member';

export interface User {
  id: string;
  name: string;
  email: string;
  department_id: string;
  department_name: string;
  role: UserRole;
  avatar?: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
}

// ========== 任务 ==========
export type TaskStatus =
  | 'pending'
  | 'claimed'
  | 'assigned_auto'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'dead'
  | 'suspected';

export type AssignmentStrategy = 'manual' | 'auto' | 'hybrid';
export type Priority = 1 | 2 | 3 | 4 | 5;

export interface Task {
  id: string;
  title: string;
  description?: string;
  department_id: string;
  department_name?: string;
  assignee_id?: string;
  assignee_name?: string;
  priority: Priority;
  status: TaskStatus;
  assignment_strategy: AssignmentStrategy;
  recommended_model?: string;
  override_model?: string;
  progress_seq?: number;
  progress_pct?: number;
  result_url?: string;
  file_hash?: string;
  output_format?: string;
  created_by?: string;
  created_at: string;
  claimed_at?: string;
  started_at?: string;
  completed_at?: string;
}

// ========== 模型 ==========
export interface ModelOption {
  id: string;
  name: string;
  model_type: 'local' | 'api';
  cost_per_call: number;
  avg_latency_ms: number;
  is_installed: boolean;
  is_locked: boolean;
  deploy_location: string;
}

// ========== 共享库 ==========
export interface SharedResult {
  id: string;
  task_id: string;
  title?: string;
  source_department_id: string;
  source_department_name?: string;
  target_department_id?: string;
  target_user_id?: string;
  approval_status: 'pending' | 'approved' | 'rejected';
  approved_by?: string;
  file_url: string;
  file_hash?: string;
  output_format?: string;
  created_at: string;
}

// ========== 通知 ==========
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'system' | 'task' | 'share';
  is_read: boolean;
  created_at: string;
}

// ========== API 通用 ==========
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiResponse<T = unknown> {
  status: string;
  data?: T;
  message?: string;
  request_id: string;
  error_code?: string;
}
