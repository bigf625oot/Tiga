import { api } from '@/core/api/client';

export interface DataSource {
  id: number;
  name: string;
  type: string;
  host?: string;
  port?: number;
  username?: string;
  database?: string;
  db_schema?: string;
  description?: string;
  url?: string;
  config?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  last_synced_at?: string;
}

export interface DataSourceCreate {
  name: string;
  type: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  database?: string;
  db_schema?: string;
  description?: string;
  url?: string;
  api_key?: string;
  private_key?: string;
  token?: string;
  config?: Record<string, any>;
}

export interface DataSourceTestResult {
  success: boolean;
  message: string;
  error_type?: string;
}

export const dataSourceApi = {
  // List all data sources
  list: async (params?: { skip?: number; limit?: number }) => {
    const response = await api.get<DataSource[]>('/data-sources/', { params });
    return response.data;
  },

  // Create a new data source
  create: async (data: DataSourceCreate) => {
    const response = await api.post<DataSource>('/data-sources/', data);
    return response.data;
  },

  // Update an existing data source
  update: async (id: number, data: Partial<DataSourceCreate>) => {
    const response = await api.put<DataSource>(`/data-sources/${id}`, data);
    return response.data;
  },

  // Delete a data source
  delete: async (id: number) => {
    const response = await api.delete<DataSource>(`/data-sources/${id}`);
    return response.data;
  },

  // Test connection
  testConnection: async (data: DataSourceCreate) => {
    const response = await api.post<DataSourceTestResult>('/data-sources/test', data);
    return response.data;
  },

  // Fetch metadata
  fetchMetadata: async (id: number) => {
    const response = await api.get<any[]>(`/data-sources/${id}/metadata`);
    return response.data;
  }
};
