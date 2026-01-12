import { 
  Task, 
  TaskCreate, 
  TaskUpdate, 
  NaturalLanguageTaskCreate, 
  APIResponse, 
  TaskListResponse 
} from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private async fetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data: APIResponse<T> = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || data.error?.message || 'API request failed');
    }

    return data.data;
  }

  // Task Endpoints
  async getTasks(params?: { 
    status?: string; 
    priority?: string; 
    skip?: number; 
    limit?: number 
  }): Promise<TaskListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.priority) query.append('priority', params.priority);
    if (params?.skip) query.append('skip', params.skip.toString());
    if (params?.limit) query.append('limit', params.limit.toString());

    return this.fetch<TaskListResponse>(`/tasks?${query.toString()}`);
  }

  async createTask(task: TaskCreate): Promise<Task> {
    return this.fetch<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  async createTaskNaturalLanguage(input: NaturalLanguageTaskCreate): Promise<Task> {
    return this.fetch<Task>('/tasks/nl-create', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async updateTask(id: number, updates: TaskUpdate): Promise<Task> {
    return this.fetch<Task>(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteTask(id: number): Promise<void> {
    return this.fetch<void>(`/tasks/${id}`, {
      method: 'DELETE',
    });
  }

  async completeTask(id: number, actualDuration?: number): Promise<Task> {
    const query = actualDuration ? `?actual_duration=${actualDuration}` : '';
    return this.fetch<Task>(`/tasks/${id}/complete${query}`, {
      method: 'POST',
    });
  }

  async breakdownTask(id: number, titles?: string[]): Promise<Task[]> {
    return this.fetch<Task[]>(`/tasks/${id}/breakdown`, {
      method: 'POST',
      body: JSON.stringify(titles || null), // Send null if no titles to trigger AI generation
    });
  }

  async suggestBreakdown(id: number): Promise<string[]> {
    return this.fetch<string[]>(`/tasks/${id}/breakdown/suggest`);
  }

  async scheduleTask(id: number): Promise<any> {
    return this.fetch<any>(`/tasks/${id}/schedule`, { method: 'POST' });
  }

  async getTaskStatistics(): Promise<any> {
    return this.fetch<any>('/tasks/statistics');
  }

  async chatWithAgent(message: string): Promise<string> {
    return this.fetch<string>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
}

export const api = new ApiClient();
