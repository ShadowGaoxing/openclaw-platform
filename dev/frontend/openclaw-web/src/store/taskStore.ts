import { create } from 'zustand';
import type { Task, PaginatedResponse, TaskStatus } from '../types';

interface TaskStore {
  tasks: Task[];
  total: number;
  currentPage: number;
  activeTab: TaskStatus | 'all';
  isLoading: boolean;
  setTasks: (response: PaginatedResponse<Task>) => void;
  setActiveTab: (tab: TaskStatus | 'all') => void;
  setLoading: (loading: boolean) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, partial: Partial<Task>) => void;
  unreadCount: number;
  setUnreadCount: (count: number) => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
  tasks: [],
  total: 0,
  currentPage: 1,
  activeTab: 'all',
  isLoading: false,
  unreadCount: 0,

  setTasks: (response) =>
    set({
      tasks: response.items,
      total: response.total,
      currentPage: response.page,
    }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  setLoading: (loading) => set({ isLoading: loading }),

  addTask: (task) =>
    set((state) => ({ tasks: [task, ...state.tasks] })),

  updateTask: (id, partial) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === id ? { ...t, ...partial } : t
      ),
    })),

  setUnreadCount: (count) => set({ unreadCount: count }),
}));
