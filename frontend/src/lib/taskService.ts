import { Task, CreateTaskInput, UpdateTaskInput } from '@/types/task';
import { supabase, isSupabaseConfigured } from './supabase';

const API_BASE_URL = 'http://localhost:8000/api';

const getAuthHeaders = async () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (isSupabaseConfigured && supabase) {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
      return headers;
    }
  }

  // Fallback to mock session token if running locally without Supabase configured
  if (typeof window !== 'undefined') {
    const storedUser = localStorage.getItem('task-tracker-mock-user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        if (parsed && parsed.email) {
          headers['Authorization'] = `Bearer mock-session-${parsed.email}`;
        }
      } catch (e) {
        // Ignore
      }
    }
  }

  return headers;
};

export const taskService = {
  async testConnection(): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        return { success: false, error: `Backend API responded with ${response.status}` };
      }
      const data = await response.json();
      return { 
        success: data.database === 'connected', 
        error: data.error || (data.database !== 'connected' ? 'Supabase is not configured on Backend' : undefined) 
      };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to connect to Backend Server' };
    }
  },

  async fetchTasks(userId: string): Promise<Task[]> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/tasks`, {
        method: 'GET',
        headers
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch tasks: ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      console.error('API fetch failed:', err);
      return [];
    }
  },

  async addTask(input: CreateTaskInput, userId: string): Promise<Task> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      headers,
      body: JSON.stringify(input)
    });
    if (!response.ok) {
      throw new Error(`Failed to add task: ${response.statusText}`);
    }
    return await response.json();
  },

  async updateTask(id: string, updates: UpdateTaskInput, userId: string): Promise<Task> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(updates)
    });
    if (!response.ok) {
      throw new Error(`Failed to update task: ${response.statusText}`);
    }
    return await response.json();
  },

  async deleteTask(id: string, userId: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'DELETE',
      headers
    });
    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.statusText}`);
    }
  },

  async deleteAllTasks(userId: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'DELETE',
      headers
    });
    if (!response.ok) {
      throw new Error(`Failed to clear workspace: ${response.statusText}`);
    }
  },

  async resetProfile(userId: string): Promise<Task[]> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/profile/reset`, {
      method: 'POST',
      headers
    });
    if (!response.ok) {
      throw new Error(`Failed to reset profile: ${response.statusText}`);
    }
    const data = await response.json();
    return data.tasks || [];
  }
};
