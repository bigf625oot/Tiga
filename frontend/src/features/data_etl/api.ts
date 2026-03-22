import { api } from '@/core/api/client';

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  file_count: number;
  folder_count: number;
  status: 'active' | 'inactive';
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
  status?: 'active' | 'inactive';
}

export interface KnowledgeBaseUpdate {
  name?: string;
  description?: string;
  status?: 'active' | 'inactive';
}

export interface KnowledgeFile {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size?: string;
  parent_id?: string;
  children?: KnowledgeFile[];
  created_at: string;
  authorized_roles: string[];
  authorized_users: string[];
}

export interface KnowledgeBaseConfig {
  enable_rag: boolean;
  enable_kg: boolean;
  chunk_size: number;
  embedding_model: string;
  retrieval_strategy: 'hybrid' | 'vector' | 'keyword';
  max_file_size: number;
  allowed_file_types: string[];
}

export interface KnowledgeBasePermission {
  roles: string[];
  users: string[];
}

export const knowledgeBaseApi = {
  list: async (params?: { skip?: number; limit?: number; query?: string }) => {
    const response = await api.get<KnowledgeBase[]>('/knowledge-bases/', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<KnowledgeBase>(`/knowledge-bases/${id}`);
    return response.data;
  },

  create: async (data: KnowledgeBaseCreate) => {
    const response = await api.post<KnowledgeBase>('/knowledge-bases/', data);
    return response.data;
  },

  update: async (id: string, data: KnowledgeBaseUpdate) => {
    const response = await api.put<KnowledgeBase>(`/knowledge-bases/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/knowledge-bases/${id}`);
  },

  getFiles: async (id: string, params?: { parent_id?: string }) => {
    const response = await api.get<KnowledgeFile[]>(`/knowledge-bases/${id}/files`, { params });
    return response.data;
  },

  createFile: async (id: string, data: { name: string; type: 'file' | 'folder'; parent_id?: string }) => {
    const response = await api.post<KnowledgeFile>(`/knowledge-bases/${id}/files`, data);
    return response.data;
  },

  updateFile: async (kbId: string, fileId: string, data: Partial<KnowledgeFile>) => {
    const response = await api.put<KnowledgeFile>(`/knowledge-bases/${kbId}/files/${fileId}`, data);
    return response.data;
  },

  deleteFile: async (kbId: string, fileId: string) => {
    await api.delete(`/knowledge-bases/${kbId}/files/${fileId}`);
  },

  uploadFile: async (kbId: string, file: File, parentId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (parentId) formData.append('parent_id', parentId);
    const response = await api.post<KnowledgeFile>(`/knowledge-bases/${kbId}/files/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getConfig: async (id: string) => {
    const response = await api.get<KnowledgeBaseConfig>(`/knowledge-bases/${id}/config`);
    return response.data;
  },

  updateConfig: async (id: string, data: KnowledgeBaseConfig) => {
    const response = await api.put<KnowledgeBaseConfig>(`/knowledge-bases/${id}/config`, data);
    return response.data;
  },

  getPermissions: async (id: string) => {
    const response = await api.get<KnowledgeBasePermission>(`/knowledge-bases/${id}/permissions`);
    return response.data;
  },

  updatePermissions: async (id: string, data: KnowledgeBasePermission) => {
    await api.put(`/knowledge-bases/${id}/permissions`, data);
  },
};

export interface Department {
  id: string;
  name: string;
  code: string;
  parent_id: string | null;
  parent?: Department;
  description?: string;
  leader?: string;
  phone?: string;
  userCount: number;
  created_at?: string;
  updated_at?: string;
  children?: Department[];
  _level?: number;
  _path?: string[];
}

export interface DepartmentCreate {
  name: string;
  code: string;
  description?: string;
  leader?: string;
  phone?: string;
  parent_id?: string;
}

export interface DepartmentUpdate {
  name?: string;
  code?: string;
  description?: string;
  leader?: string;
  phone?: string;
  parent_id?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  role_id: string;
  department_id?: string;
  status: boolean;
  created_at?: string;
  updated_at?: string;
  department?: Department;
}

export interface UserPage {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

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

export interface ContextManagementConfig {
  history_limit: number;
  compression_threshold: number;
  enable_graph_memory: boolean;
  graph_hop_depth: number;
}

export interface MemoryManagementConfig {
  enable_session_kb: boolean;
  embedding_model_id: string;
  memory_extraction_interval: number;
}

export interface ContextMemoryConfig {
  version: number;
  context: ContextManagementConfig;
  memory: MemoryManagementConfig;
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
    const response = await api.get<any[]>(`/data-sources/${id}/tables/${tableName}/preview`, { params: { limit } });
    return response.data;
  },

  // Preview custom SQL query
  previewQuery: async (id: number, query: string, limit: number = 10) => {
    const response = await api.post<any[]>(`/data-sources/${id}/query/preview`, { query }, { params: { limit } });
    return response.data;
  }
};

export interface Role {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_system: boolean;
  userCount: number;
  permissions: string[];
}

export interface RoleCreate {
  name: string;
  code: string;
  description?: string;
  is_system?: boolean;
  permissions?: string[];
}

export interface RoleUpdate {
  name?: string;
  code?: string;
  description?: string;
  is_system?: boolean;
  permissions?: string[];
}

export const roleApi = {
  list: async () => {
    const response = await api.get<Role[]>('/users/roles');
    return response.data;
  },
  create: async (data: RoleCreate) => {
    const response = await api.post<Role>('/users/roles', data);
    return response.data;
  },
  update: async (id: string, data: RoleUpdate) => {
    const response = await api.put<Role>(`/users/roles/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await api.delete(`/users/roles/${id}`);
    return response.data;
  },
};

export const systemConfigApi = {
  getContextMemory: async () => {
    const response = await api.get<ContextMemoryConfig>('/system-config/context-memory');
    return response.data;
  },
  updateContextMemory: async (payload: ContextMemoryConfig) => {
    const response = await api.put<ContextMemoryConfig>('/system-config/context-memory', payload);
    return response.data;
  },
  resetContextMemory: async () => {
    const response = await api.delete<ContextMemoryConfig>('/system-config/context-memory');
    return response.data;
  },
};

export const departmentApi = {
  list: async (params?: { skip?: number; limit?: number }) => {
    const response = await api.get<Department[]>('/departments/', { params });
    return response.data;
  },
  create: async (data: DepartmentCreate) => {
    const response = await api.post<Department>('/departments/', data);
    return response.data;
  },
  update: async (id: string, data: DepartmentUpdate) => {
    const response = await api.put<Department>(`/departments/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await api.delete<Department>(`/departments/${id}`);
    return response.data;
  },
  get: async (id: string) => {
    const response = await api.get<Department>(`/departments/${id}`);
    return response.data;
  },
  listUsers: async (params?: { page?: number; page_size?: number; query?: string }) => {
    const response = await api.get<UserPage>('/users/', { params });
    return response.data;
  },
  transferUsers: async (departmentId: string, userIds: string[]) => {
    const response = await api.post('/users/bulk-transfer-department', {
      user_ids: userIds,
      department_id: departmentId
    });
    return response.data;
  }
};
