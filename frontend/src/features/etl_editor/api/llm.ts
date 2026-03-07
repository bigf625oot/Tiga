import { api } from '@/core/api/client';

export interface Model {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  model_type: string;
  is_active: boolean;
}

export const llmApi = {
  // Get all available models
  listModels: async () => {
    const response = await api.get<Model[]>('/llm/models');
    return response.data;
  }
};
