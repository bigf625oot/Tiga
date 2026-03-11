import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { usePipelineStore } from '../usePipelineStore';
import { pipelineApi } from '../../api/pipeline';
import { PipelineStatus } from '../../types/pipeline';

// Mock the API
vi.mock('../../api/pipeline', () => ({
  pipelineApi: {
    list: vi.fn(),
    delete: vi.fn(),
    run: vi.fn(),
    stop: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  }
}));

describe('usePipelineStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetchPipelines should update pipelines state', async () => {
    const store = usePipelineStore();
    const mockPipelines = [
      { id: 1, name: 'Test Pipeline', status: PipelineStatus.CREATED },
      { id: 2, name: 'Another Pipeline', status: PipelineStatus.RUNNING }
    ];
    (pipelineApi.list as any).mockResolvedValue(mockPipelines);

    await store.fetchPipelines();

    expect(store.pipelines).toEqual(mockPipelines);
    expect(store.loading).toBe(false);
  });

  it('deletePipeline should remove pipeline from state', async () => {
    const store = usePipelineStore();
    store.pipelines = [
      { id: 1, name: 'Test Pipeline', status: PipelineStatus.CREATED } as any,
      { id: 2, name: 'Another Pipeline', status: PipelineStatus.RUNNING } as any
    ];
    
    (pipelineApi.delete as any).mockResolvedValue({ success: true });

    await store.deletePipeline(1);

    expect(store.pipelines).toHaveLength(1);
    expect(store.pipelines[0].id).toBe(2);
    expect(pipelineApi.delete).toHaveBeenCalledWith(1);
  });

  it('runPipeline should update status', async () => {
    const store = usePipelineStore();
    store.currentPipeline = { id: 1, name: 'Test', status: PipelineStatus.CREATED } as any;
    
    (pipelineApi.update as any).mockResolvedValue({ id: 1 });
    (pipelineApi.run as any).mockResolvedValue({ status: 'success' });
    
    // Mock get for polling
    (pipelineApi.get as any).mockResolvedValue({ id: 1, status: PipelineStatus.RUNNING });

    await store.runPipeline();

    expect(store.currentPipeline?.status).toBe(PipelineStatus.RUNNING);
    expect(pipelineApi.run).toHaveBeenCalledWith(1);
  });

  it('stopPipeline should update status', async () => {
    const store = usePipelineStore();
    store.currentPipeline = { id: 1, name: 'Test', status: PipelineStatus.RUNNING } as any;
    
    (pipelineApi.stop as any).mockResolvedValue({ success: true });

    await store.stopPipeline();

    expect(store.currentPipeline?.status).toBe(PipelineStatus.STOPPED);
    expect(pipelineApi.stop).toHaveBeenCalledWith(1);
  });
});
