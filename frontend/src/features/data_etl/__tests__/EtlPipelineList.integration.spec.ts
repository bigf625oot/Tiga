import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import EtlPipelineList from '../EtlPipelineList.vue'
import { pipelineApi } from '@/features/etl_editor/api/pipeline'
import { PipelineStatus } from '@/features/etl_editor/types/pipeline'

// Mock API
vi.mock('@/features/etl_editor/api/pipeline', () => ({
  pipelineApi: {
    list: vi.fn(),
    delete: vi.fn(),
    run: vi.fn(),
    stop: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  }
}))

// Mock components (keep UI mocks)
vi.mock('@/components/ui/button', () => ({
  Button: { template: '<button @click="$emit(\'click\')"><slot /></button>' }
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

describe('EtlPipelineList Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches pipelines on mount', async () => {
    const mockPipelines = [
      { id: 1, name: 'Integration Pipeline', status: PipelineStatus.CREATED, created_at: '2023-01-01' }
    ];
    (pipelineApi.list as any).mockResolvedValue(mockPipelines);

    const wrapper = mount(EtlPipelineList, {
      global: {
        plugins: [createPinia()],
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
    });

    // Wait for promises
    await new Promise(resolve => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    expect(pipelineApi.list).toHaveBeenCalled();
    expect(wrapper.text()).toContain('Integration Pipeline');
  })
})
