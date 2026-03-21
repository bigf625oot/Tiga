import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ContextMemoryConfig from '../ContextMemoryConfig.vue'

const mockApi = vi.hoisted(() => ({
  getContextMemory: vi.fn(),
  updateContextMemory: vi.fn(),
  resetContextMemory: vi.fn(),
}))

vi.mock('@/features/data_etl/api', () => ({
  systemConfigApi: mockApi,
}))

vi.mock('@/components/ui/toast/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

vi.mock('@/components/ui/button', () => ({
  Button: { template: '<button v-bind="$attrs"><slot /></button>' },
}))
vi.mock('@/components/ui/card', () => ({
  Card: { template: '<div><slot /></div>' },
  CardHeader: { template: '<div><slot /></div>' },
  CardTitle: { template: '<div><slot /></div>' },
  CardDescription: { template: '<div><slot /></div>' },
  CardContent: { template: '<div><slot /></div>' },
}))
vi.mock('@/components/ui/input', () => ({
  Input: { template: '<input v-bind="$attrs" />', props: ['modelValue'], emits: ['update:modelValue'] },
}))
vi.mock('@/components/ui/label', () => ({
  Label: { template: '<label><slot /></label>' },
}))
vi.mock('@/components/ui/switch', () => ({
  Switch: { template: '<input type="checkbox" v-bind="$attrs" />', props: ['checked'], emits: ['update:checked'] },
}))

describe('ContextMemoryConfig.vue', () => {
  beforeEach(() => {
    mockApi.getContextMemory.mockResolvedValue({
      version: 1,
      context: { history_limit: 10, compression_threshold: 3000, enable_graph_memory: true, graph_hop_depth: 1 },
      memory: { enable_session_kb: true, embedding_model_id: 'text-embedding-3-small', memory_extraction_interval: 10 },
    })
    mockApi.updateContextMemory.mockResolvedValue({
      version: 1,
      context: { history_limit: 10, compression_threshold: 3000, enable_graph_memory: true, graph_hop_depth: 1 },
      memory: { enable_session_kb: true, embedding_model_id: 'text-embedding-3-small', memory_extraction_interval: 10 },
    })
    mockApi.resetContextMemory.mockResolvedValue({
      version: 1,
      context: { history_limit: 10, compression_threshold: 3000, enable_graph_memory: true, graph_hop_depth: 1 },
      memory: { enable_session_kb: true, embedding_model_id: 'text-embedding-3-small', memory_extraction_interval: 10 },
    })
  })

  it('loads config on mount', async () => {
    mount(ContextMemoryConfig)
    await flushPromises()
    expect(mockApi.getContextMemory).toHaveBeenCalledTimes(1)
  })

  it('saves config when clicking save', async () => {
    const wrapper = mount(ContextMemoryConfig)
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('保存配置'))?.trigger('click')
    await flushPromises()

    expect(mockApi.updateContextMemory).toHaveBeenCalledTimes(1)
  })

  it('resets config when clicking reset', async () => {
    const wrapper = mount(ContextMemoryConfig)
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('恢复默认'))?.trigger('click')
    await flushPromises()

    expect(mockApi.resetContextMemory).toHaveBeenCalledTimes(1)
  })
})
