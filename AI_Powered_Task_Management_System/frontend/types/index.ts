export type Priority = 'low' | 'medium' | 'high';
export type TaskStatus = 'todo' | 'in_progress' | 'completed';

export interface Tag {
  id: number;
  name: string;
  color?: string;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: Priority;
  due_date?: string;
  estimated_duration?: number; // minutes
  actual_duration?: number; // minutes
  created_at: string;
  updated_at: string;
  completed_at?: string;
  user_id: number;
  parent_task_id?: number | null;
  tags: Tag[];
  subtasks: Task[];
  task_metadata?: Record<string, any>;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: Priority;
  due_date?: string; // ISO string
  estimated_duration?: number;
  tag_ids?: number[];
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: Priority;
  due_date?: string;
  estimated_duration?: number;
  actual_duration?: number;
  tag_ids?: number[];
}

export interface NaturalLanguageTaskCreate {
  message: string;
  context?: Record<string, any>;
}

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
