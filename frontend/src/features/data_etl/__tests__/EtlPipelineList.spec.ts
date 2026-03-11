import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import EtlPipelineList from '../EtlPipelineList.vue'

// Mock the store hook
const mockPipelineStore = {
  loading: true,
  pipelines: [],
  fetchPipelines: vi.fn(),
  deletePipeline: vi.fn(),
  runPipeline: vi.fn(),
  stopPipeline: vi.fn(),
  initializeTemplate: vi.fn(),
}

vi.mock('@/features/etl_editor/composables/usePipelineStore', () => ({
  usePipelineStore: () => mockPipelineStore
}))

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

// Mock config
vi.mock('@/features/etl_editor/config/templates', () => ({
  PIPELINE_TEMPLATES: []
}))

describe('EtlPipelineList.vue', () => {
  it('renders skeleton when loading', () => {
    mockPipelineStore.loading = true;
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
          Checkbox: true,
          Dialog: true,
          DialogContent: true,
          DialogHeader: true,
          DialogTitle: true,
          DialogDescription: true,
          Card: true,
          CardHeader: true,
          CardTitle: true,
          CardContent: true,
          AlertDialog: true,
          AlertDialogContent: true,
          AlertDialogHeader: true,
          AlertDialogTitle: true,
          AlertDialogDescription: true,
          AlertDialogFooter: true,
          AlertDialogCancel: true,
          AlertDialogAction: true
        }
      }
    })
    
    expect(wrapper.find('.skeleton-etl').exists()).toBe(true)
  })

  it('renders pipelines when loaded', async () => {
    mockPipelineStore.loading = false;
    mockPipelineStore.pipelines = [
        { id: 1, name: 'Test Pipeline', status: 'running', created_at: '2023-01-01', last_run_at: '2023-01-02' }
    ] as any;

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
            Checkbox: true,
            Dialog: true,
            DialogContent: true,
            DialogHeader: true,
            DialogTitle: true,
            DialogDescription: true,
            Card: true,
            CardHeader: true,
            CardTitle: true,
            CardContent: true,
            AlertDialog: true,
            AlertDialogContent: true,
            AlertDialogHeader: true,
            AlertDialogTitle: true,
            AlertDialogDescription: true,
            AlertDialogFooter: true,
            AlertDialogCancel: true,
            AlertDialogAction: true
        }
      }
    })
    
    expect(wrapper.find('.skeleton-etl').exists()).toBe(false)
    expect(wrapper.text()).toContain('Test Pipeline')
  })
})
