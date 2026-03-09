import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SearchAgent from '../SearchAgent.vue'
import axios from 'axios'
import { createPinia } from 'pinia'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
    })),
  },
}))

// Mock useToast
const mockToast = vi.fn()
vi.mock('@/components/ui/toast/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}))

// Mock ResizeObserver for ScrollArea
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('SearchAgent.vue', () => {
  let wrapper: any
  let mockPost: any

  beforeEach(() => {
    vi.clearAllMocks()
    mockPost = vi.fn()
    ;(axios.create as any).mockReturnValue({
      post: mockPost,
    })

    wrapper = mount(SearchAgent, {
      global: {
        plugins: [createPinia()],
        stubs: {
          // Stub complex UI components if needed, or use shallowMount
          // For integration tests, we mount fully but stub icons/external deps
          LucideVueNext: true, 
        },
      },
    })
  })

  it('renders initial state correctly', () => {
    expect(wrapper.text()).toContain('全网智能检索')
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    expect(wrapper.find('button').text()).toContain('立即搜索')
  })

  it('disables search button when query is empty', async () => {
    const button = wrapper.find('button')
    expect(button.attributes('disabled')).toBeDefined()
    
    await wrapper.find('input[type="text"]').setValue('test query')
    expect(button.attributes('disabled')).toBeUndefined()
  })

  it('performs search on button click', async () => {
    let resolvePost: any
    const postPromise = new Promise(r => resolvePost = r)
    mockPost.mockReturnValue(postPromise)

    await wrapper.find('input[type="text"]').setValue('test query')
    await wrapper.find('button').trigger('click')

    expect(wrapper.vm.loading).toBe(true)
    
    resolvePost({
      data: {
        success: true,
        data: {
          results: [
            {
              title: 'Test Result',
              url: 'http://example.com',
              content: 'Test Content',
              source: 'Test Source',
              news_time: '2024-01-01',
              tier: 'global',
            },
          ],
        },
      },
    })
    
    await flushPromises()
    expect(wrapper.vm.loading).toBe(false)
    
    expect(mockPost).toHaveBeenCalledWith('/news_search/search', expect.objectContaining({
      keywords: ['test query'],
    }))
    
    expect(wrapper.text()).toContain('Test Result')
    expect(wrapper.text()).toContain('Test Content')
  })

  it('shows error message on failure', async () => {
    mockPost.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'API Error',
        },
      },
    })

    await wrapper.find('input[type="text"]').setValue('test query')
    await wrapper.find('button').trigger('click')
    
    await flushPromises()
    
    expect(wrapper.text()).toContain('API Error')
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      variant: 'destructive',
    }))
  })

  it('toggles advanced options', async () => {
    expect(wrapper.find('.grid-cols-1').exists()).toBe(false) // Panel hidden initially
    
    // Find trigger button for advanced options
    const triggers = wrapper.findAll('button')
    const advancedTrigger = triggers.find((b: any) => b.text().includes('高级筛选'))
    
    await advancedTrigger.trigger('click')
    
    // Wait for animation/state update
    await wrapper.vm.$nextTick()
    
    // Check if form fields are visible (might need to check if content is rendered)
    // Since Collapsible usually uses v-show or v-if, and we use shadcn Collapsible
    // The content is always in DOM but hidden or not mounted?
    // With shallow mount or full mount, checking component state 'showAdvanced' is safer
    expect(wrapper.vm.showAdvanced).toBe(true)
  })

  it('uses advanced search API when options are used', async () => {
    wrapper.vm.showAdvanced = true
    await wrapper.vm.$nextTick()
    
    wrapper.vm.advancedForm.timeRange = '最近一周'
    
    mockPost.mockResolvedValueOnce({
      data: { success: true, data: { results: [] } },
    })

    await wrapper.find('input[type="text"]').setValue('test query')
    await wrapper.find('button').trigger('click')
    
    await flushPromises()
    
    expect(mockPost).toHaveBeenCalledWith('/news_search/custom_search', expect.objectContaining({
      time_range: '最近一周',
    }))
  })
})
