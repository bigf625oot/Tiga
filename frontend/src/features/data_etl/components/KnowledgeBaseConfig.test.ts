import { shallowMount, flushPromises } from '@vue/test-utils';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import KnowledgeBaseConfig from './KnowledgeBaseConfig.vue';

vi.mock('../services/knowledgeBaseService', () => {
  return {
    knowledgeBaseService: {
      getKnowledgeBases: vi.fn().mockResolvedValue([]),
      getFiles: vi.fn().mockResolvedValue([]),
      getConfig: vi.fn().mockResolvedValue({
        enable_rag: true,
        enable_kg: true,
        chunk_size: 512,
        embedding_model: 'text-embedding-3-small',
        retrieval_strategy: 'hybrid',
        max_file_size: 100,
        allowed_file_types: ['.pdf'],
      }),
      getPermissions: vi.fn().mockResolvedValue({ roles: [], users: [] }),
      renameFile: vi.fn(),
    },
  };
});

describe('KnowledgeBaseConfig - 文件夹重命名', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue([]),
    } as any);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('打开重命名对话框并预填名称', async () => {
    const wrapper = shallowMount(KnowledgeBaseConfig) as any;
    wrapper.vm.activeKnowledgeBaseId = 'kb1';
    await flushPromises();
    wrapper.vm.currentFiles = [
      {
        id: 'f1',
        name: '旧文件夹',
        type: 'folder',
        parent_id: undefined,
        children: [],
        size: undefined,
        created_at: '2020-01-01T00:00:00Z',
        authorized_roles: [],
        authorized_users: [],
      },
    ];

    wrapper.vm.openRenameDialog('f1');
    await flushPromises();

    expect(wrapper.vm.isRenameDialogOpen).toBe(true);
    expect(wrapper.vm.renameForm.name).toBe('旧文件夹');
  });

  it('提交重命名会调用服务并更新本地名称', async () => {
    const { knowledgeBaseService } = await import('../services/knowledgeBaseService');
    knowledgeBaseService.renameFile = vi.fn().mockResolvedValue({
      id: 'f1',
      name: '新文件夹',
      type: 'folder',
      parent_id: undefined,
      children: [],
      size: undefined,
      created_at: '2020-01-01T00:00:00Z',
      authorized_roles: [],
      authorized_users: [],
    });

    const wrapper = shallowMount(KnowledgeBaseConfig) as any;
    wrapper.vm.activeKnowledgeBaseId = 'kb1';
    await flushPromises();
    wrapper.vm.currentFiles = [
      {
        id: 'f1',
        name: '旧文件夹',
        type: 'folder',
        parent_id: undefined,
        children: [],
        size: undefined,
        created_at: '2020-01-01T00:00:00Z',
        authorized_roles: [],
        authorized_users: [],
      },
    ];

    wrapper.vm.openRenameDialog('f1');
    await flushPromises();

    wrapper.vm.renameForm.name = '新文件夹';
    await wrapper.vm.handleRename();
    await flushPromises();

    expect(knowledgeBaseService.renameFile).toHaveBeenCalledWith('kb1', 'f1', '新文件夹');
    expect(wrapper.vm.currentFiles[0].name).toBe('新文件夹');
    expect(wrapper.vm.isRenameDialogOpen).toBe(false);
    expect(wrapper.vm.renameForm.name).toBe('');
  });
});
