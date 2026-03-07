import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import EtlPipelineList from '../EtlPipelineList.vue'

// Mock components
vi.mock('@/components/ui/button', () => ({
  Button: { template: '<button><slot /></button>' }
}))
vi.mock('@/components/ui/input', () => ({
  Input: { template: '<input />', props: ['modelValue'], emits: ['update:modelValue'] }
}))
vi.mock('@/components/ui/badge', () => ({
  Badge: { template: '<span><slot /></span>' }
}))
vi.mock('@/components/ui/table', () => ({
  Table: { template: '<table><slot /></table>' },
  TableHeader: { template: '<thead><slot /></thead>' },
  TableBody: { template: '<tbody><slot /></tbody>' },
  TableRow: { template: '<tr><slot /></tr>' },
  TableHead: { template: '<th><slot /></th>' },
  TableCell: { template: '<td><slot /></td>' },
}))
vi.mock('@/components/skeletons', () => ({
  SkeletonETL: { template: '<div class="skeleton-etl"></div>' }
}))
vi.mock('@/components/ui/toast', () => ({
  useToast: () => ({ toast: vi.fn() })
}))

describe('EtlPipelineList.vue', () => {
  it('renders skeleton when loading', () => {
    const wrapper = mount(EtlPipelineList, {
      global: {
        stubs: {
          DropdownMenu: true,
          DropdownMenuTrigger: true,
          DropdownMenuContent: true,
          DropdownMenuItem: true,
          DropdownMenuSeparator: true,
          Search: true,
          Filter: true,
          ChevronDown: true,
          Trash2: true,
          RefreshCw: true,
          ArrowUpDown: true,
          Plus: true,
          MoreHorizontal: true,
          Pencil: true,
          Copy: true,
          Play: true,
          Pause: true,
          Checkbox: true
        }
      }
    })
    
    // Initially loading is true
    expect(wrapper.find('.skeleton-etl').exists()).toBe(true)
  })
})
