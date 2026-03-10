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
  },

  // Fetch columns
  fetchColumns: async (id: number, tableName: string) => {
    const response = await api.get<string[]>(`/data-sources/${id}/tables/${tableName}/columns`);
    return response.data;
  },

  // Preview table data
  previewTable: async (id: number, tableName: string, limit: number = 10) => {
    // We'll use a new endpoint or adapt existing one.
    // For now, let's assume we add a preview endpoint in backend or reuse fetch_data
    // Since we don't have backend modification permission right now in this turn (conceptually),
    // we will add the frontend method and I'll add the backend endpoint next.
    const response = await api.get<any[]>(`/data-sources/${id}/tables/${tableName}/preview`, { params: { limit } });
    return response.data;
  },

  // Preview custom SQL query
  previewQuery: async (id: number, query: string, limit: number = 10) => {
    const response = await api.post<any[]>(`/data-sources/${id}/query/preview`, { query }, { params: { limit } });
    return response.data;
  }
};
