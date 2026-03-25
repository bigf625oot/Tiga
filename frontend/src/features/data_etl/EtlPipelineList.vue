<template>
  <div class="h-full flex flex-col bg-background overflow-hidden">
    <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold tracking-tight">ETL 流水线管理</h2>
        <div class="h-4 w-px bg-border"></div>
        <p class="text-xs text-muted-foreground m-0 truncate max-w-xl">管理和监控所有数据处理流程。</p>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar bg-muted/10 flex flex-col">
      <div class="w-full flex flex-col gap-8 flex-1">
        <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
          <div class="hidden md:block w-full md:w-64"></div>

          <div class="flex items-center justify-center flex-1 gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="outline" size="sm" class="h-9 gap-2 shadow-sm">
                  <Filter class="w-4 h-4" />
                  {{ filterStatus ? getStatusLabel(filterStatus) : '所有状态' }}
                  <ChevronDown class="w-4 h-4 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="center">
                <DropdownMenuItem @click="filterStatus = ''">所有状态</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="filterStatus = 'running'">运行中</DropdownMenuItem>
                <DropdownMenuItem @click="filterStatus = 'stopped'">已停止</DropdownMenuItem>
                <DropdownMenuItem @click="filterStatus = 'created'">已创建</DropdownMenuItem>
                <DropdownMenuItem @click="filterStatus = 'failed'">失败</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="outline" size="sm" class="h-9 gap-2 shadow-sm">
                  <ArrowUpDown class="w-4 h-4" />
                  {{ sortByLabel }}
                  <ChevronDown class="w-4 h-4 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="center">
                <DropdownMenuItem @click="setSort('created_at')">创建时间</DropdownMenuItem>
                <DropdownMenuItem @click="setSort('last_run_at')">最近运行</DropdownMenuItem>
                <DropdownMenuItem @click="setSort('name')">名称</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="toggleSortDirection">{{ sortDirection === 'asc' ? '升序' : '降序' }}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div class="flex items-center gap-3 w-full md:w-auto justify-end">
            <div class="relative w-full md:w-64 group">
              <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              <Input v-model="searchQuery" placeholder="搜索流水线..." class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50" />
              <button v-if="searchQuery" @click="searchQuery = ''" class="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors" aria-label="清空搜索">
                <X class="h-4 w-4" />
              </button>
            </div>

            <div class="h-4 w-px bg-border hidden md:block mx-1"></div>

            <Button v-if="selectedIds.length > 0" variant="destructive" size="sm" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0" @click="batchDelete">
              <Trash2 class="w-3.5 h-3.5" />
              批量删除 ({{ selectedIds.length }})
            </Button>

            <Button @click="refreshData" variant="outline" size="icon" class="h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95 flex-shrink-0" title="刷新列表">
              <RefreshCw class="h-4 w-4 text-muted-foreground" :class="{ 'animate-spin': isRefreshing }" />
            </Button>

            <Button @click="isCreateDialogOpen = true" size="sm" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
              <Plus class="w-3.5 h-3.5" />
              新建流水线
            </Button>
          </div>
        </div>

        <div class="flex flex-col gap-6 px-6 pb-6 flex-1">
          <div v-if="searchQuery || filterStatus" class="flex items-center gap-2">
            <h3 class="text-lg font-semibold tracking-tight text-foreground">筛选结果</h3>
            <span class="text-sm text-muted-foreground">({{ filteredPipelines.length }})</span>
          </div>

          <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <div v-for="i in 8" :key="i" class="etl-skeleton-card bg-card rounded-xl border border-border/60 overflow-hidden h-[190px] p-5 space-y-3">
              <div class="flex items-center gap-4">
                <Skeleton class="h-12 w-12 rounded-xl" />
                <div class="flex-1 space-y-2">
                  <Skeleton class="h-4 w-3/4" />
                  <Skeleton class="h-3 w-1/2" />
                </div>
              </div>
              <Skeleton class="h-3 w-full" />
              <Skeleton class="h-3 w-5/6" />
            </div>
          </div>

          <div v-else-if="paginatedPipelines.length === 0" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto">
            <div class="w-14 h-14  rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
              <img src="/Placeholder/null_search.svg" alt="暂无内容" class="h-full w-full object-cover" />
            </div>
            <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">暂无符合条件的流水线</h3>
            <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">{{ (searchQuery || filterStatus) ? '请尝试更换关键词或筛选条件。' : '当前暂无流水线，您可以点击下方按钮创建一条新的流水线。' }}</p>
            <Button v-if="!searchQuery && !filterStatus" @click="isCreateDialogOpen = true" class="px-8 shadow-sm hover:scale-105 transition-transform">
              <Plus class="w-4 h-4 mr-2" />
              立即创建
            </Button>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start">
            <EtlPipelineCard
              v-for="pipeline in paginatedPipelines"
              :key="pipeline.id"
              :pipeline="pipeline"
              :selected="selectedIds.includes(pipeline.id)"
              :status-label="getStatusLabel(pipeline.status)"
              :status-badge-variant="getStatusBadgeVariant(pipeline.status)"
              :status-color-class="getStatusColor(pipeline.status)"
              :last-run-text="formatTimeAgo(pipeline.last_run_at)"
              :created-at-text="formatDate(pipeline.created_at)"
              :is-running="pipeline.status === 'running'"
              :sort-hint="sortByLabel"
              @toggleSelect="toggleSelection(pipeline.id)"
              @edit="emit('edit', pipeline)"
              @toggleStatus="togglePipelineStatus(pipeline)"
              @duplicate="duplicatePipeline(pipeline)"
              @delete="confirmDelete(pipeline)"
            />
          </div>

          <div class="flex items-center justify-between py-2" v-if="!isLoading && filteredPipelines.length > 0">
            <div class="flex items-center gap-2" @click.stop>
              <Checkbox :checked="isAllSelected" @update:checked="toggleSelectAll" aria-label="全选" />
              <span class="text-xs text-muted-foreground">全选当前页</span>
            </div>
          </div>

          <div class="flex items-center justify-between py-4" v-if="!isLoading && filteredPipelines.length > 0">
            <div class="text-sm text-muted-foreground">
              显示 {{ (currentPage - 1) * pageSize + 1 }} 到 {{ Math.min(currentPage * pageSize, filteredPipelines.length) }} 条，共 {{ filteredPipelines.length }} 条
            </div>
            <div class="flex items-center space-x-2">
              <Button variant="outline" size="sm" :disabled="currentPage === 1" @click="currentPage--">上一页</Button>
              <div class="flex items-center gap-1">
                <Button
                  v-for="page in visiblePages"
                  :key="page"
                  variant="outline"
                  size="sm"
                  class="w-8 p-0"
                  :class="{ 'bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground': currentPage === page }"
                  @click="currentPage = typeof page === 'number' ? page : currentPage"
                  :disabled="typeof page !== 'number'"
                >
                  {{ page }}
                </Button>
              </div>
              <Button variant="outline" size="sm" :disabled="currentPage === totalPages" @click="currentPage++">下一页</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <Dialog v-model:open="isCreateDialogOpen">
    <DialogContent class="sm:max-w-[800px]">
      <DialogHeader>
        <DialogTitle>新建流水线</DialogTitle>
        <DialogDescription>
          选择一个模板快速开始，或创建一个空白流水线。
        </DialogDescription>
      </DialogHeader>
      <div class="grid grid-cols-2 gap-4 py-4">
        <Card 
          v-for="template in PIPELINE_TEMPLATES" 
          :key="template.id"
          class="cursor-pointer hover:border-primary/50 transition-colors hover:bg-muted/50"
          @click="selectTemplate(template)"
        >
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">
              {{ template.name }}
            </CardTitle>
            <component :is="iconMap[template.icon]" class="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p class="text-xs text-muted-foreground">
              {{ template.description }}
            </p>
          </CardContent>
        </Card>
      </div>
    </DialogContent>
  </Dialog>

  <AlertDialog v-model:open="isDeleteDialogOpen">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>确认删除</AlertDialogTitle>
        <AlertDialogDescription>
          {{ isBatchDeleteMode 
            ? `确定要删除选中的 ${selectedIds.length} 条流水线吗？` 
            : `确定要删除流水线 "${pipelineToDelete?.name}" 吗？` 
          }}
          此操作无法撤销。
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>取消</AlertDialogCancel>
        <AlertDialogAction @click="executeDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
          确认删除
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

import { 
  Plus, Search, Filter, ChevronDown, Trash2, RefreshCw, 
  ArrowUpDown, X,
  Network, Database, Sparkles, File, FilePlus
} from 'lucide-vue-next';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/components/ui/toast';
import { usePipelineStore } from '@/features/etl_editor/composables/usePipelineStore';
import { NodeType, SourceType, TransformType, SinkType, PipelineStatus, type Pipeline } from '@/features/etl_editor/types/pipeline';
import { PIPELINE_TEMPLATES, type PipelineTemplate } from '@/features/etl_editor/config/templates';
import EtlPipelineCard from './components/EtlPipelineCard.vue';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const emit = defineEmits(['create', 'edit', 'back', 'viewDetail', 'navigate', 'navigateToExtraction']);
const { toast } = useToast();
const pipelineStore = usePipelineStore();

const isCreateDialogOpen = ref(false);

const iconMap: Record<string, any> = {
  'FilePlus': FilePlus,
  'Network': Network,
  'Sparkles': Sparkles,
  'Database': Database
};

const selectTemplate = (template: PipelineTemplate) => {
  pipelineStore.initializeTemplate(template.nodes, template.edges);
  isCreateDialogOpen.value = false;
  emit('create');
};

// State
// const pipelines = ref<Pipeline[]>([]); // Use store.pipelines
const isLoading = computed(() => pipelineStore.loading);
const isRefreshing = ref(false);
const searchQuery = ref('');
const filterStatus = ref('');
const sortBy = ref('created_at'); // Changed from createTime
const sortDirection = ref<'asc' | 'desc'>('desc');
const selectedIds = ref<number[]>([]); // Changed to number[]
const currentPage = ref(1);
const pageSize = ref(10);

const sortByLabel = computed(() => {
  const map: Record<string, string> = {
    created_at: '创建时间',
    last_run_at: '最近运行',
    name: '名称'
  }
  return map[sortBy.value] || '排序'
})

const setSort = (field: string) => {
  sortBy.value = field
  currentPage.value = 1
}

const toggleSortDirection = () => {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  currentPage.value = 1
}

// Logic
const refreshData = async () => {
  isRefreshing.value = true;
  try {
    await pipelineStore.fetchPipelines();
    toast({ title: '刷新成功', description: '数据已更新' });
  } catch (e) {
    toast({ title: '刷新失败', description: '无法获取流水线数据', variant: 'destructive' });
  } finally {
    isRefreshing.value = false;
  }
};

onMounted(() => {
  refreshData();
});

const filteredPipelines = computed(() => {
  let result = pipelineStore.pipelines;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(p => p.name.toLowerCase().includes(query) || p.id.toString().includes(query));
  }

  if (filterStatus.value) {
    result = result.filter(p => p.status === filterStatus.value);
  }

  result = [...result].sort((a, b) => {
    let valA: any = a[sortBy.value as keyof Pipeline]
    let valB: any = b[sortBy.value as keyof Pipeline]

    if (sortBy.value === 'name') {
      valA = String(valA || '').toLowerCase()
      valB = String(valB || '').toLowerCase()
    } else {
      const tsA = valA ? new Date(valA as string).getTime() : 0
      const tsB = valB ? new Date(valB as string).getTime() : 0
      valA = Number.isFinite(tsA) ? tsA : 0
      valB = Number.isFinite(tsB) ? tsB : 0
    }

    if (valA < valB) return sortDirection.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortDirection.value === 'asc' ? 1 : -1;
    return 0;
  });

  return result;
});

const totalPages = computed(() => Math.ceil(filteredPipelines.value.length / pageSize.value));

const paginatedPipelines = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredPipelines.value.slice(start, start + pageSize.value);
});

watch([searchQuery, filterStatus, sortBy, sortDirection], () => {
  currentPage.value = 1
});

const visiblePages = computed(() => {
  const total = totalPages.value;
  const current = currentPage.value;
  const delta = 2;
  const range = [];
  for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
    range.push(i);
  }
  if (current - delta > 2) range.unshift('...');
  if (current + delta < total - 1) range.push('...');
  range.unshift(1);
  if (total > 1) range.push(total);
  return range;
});

const isAllSelected = computed(() => {
  return paginatedPipelines.value.length > 0 && paginatedPipelines.value.every(p => selectedIds.value.includes(p.id));
});

// Actions
const toggleSort = (field: string) => {
  if (sortBy.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = field;
    sortDirection.value = 'desc';
  }
};

const toggleSelection = (id: number) => {
  const index = selectedIds.value.indexOf(id);
  if (index > -1) selectedIds.value.splice(index, 1);
  else selectedIds.value.push(id);
};

const toggleSelectAll = (checked: boolean) => {
  if (checked) {
    const ids = paginatedPipelines.value.map(p => p.id);
    // Add unique ids
    ids.forEach(id => {
      if (!selectedIds.value.includes(id)) selectedIds.value.push(id);
    });
  } else {
    const ids = paginatedPipelines.value.map(p => p.id);
    selectedIds.value = selectedIds.value.filter(id => !ids.includes(id));
  }
};

const togglePipelineStatus = async (pipeline: Pipeline) => {
  try {
    if (pipeline.status === PipelineStatus.RUNNING) {
      await pipelineStore.stopPipeline(pipeline.id);
      toast({ title: '流水线已暂停', description: `流水线 "${pipeline.name}" 状态已更新` });
    } else {
      await pipelineStore.runPipeline(pipeline.id);
      toast({ title: '流水线已启动', description: `流水线 "${pipeline.name}" 状态已更新` });
    }
  } catch (e) {
    toast({ title: '操作失败', description: '无法更新流水线状态', variant: 'destructive' });
  }
};

const duplicatePipeline = async (pipeline: Pipeline) => {
  try {
    await pipelineStore.createPipeline({
      name: `${pipeline.name} (副本)`,
      dag_config: pipeline.dag_config || { nodes: [], edges: [] }
    });
    toast({ title: '复制成功', description: '新流水线已创建' });
  } catch (e) {
    toast({ title: '复制失败', description: '无法创建副本', variant: 'destructive' });
  }
};

const isDeleteDialogOpen = ref(false);
const pipelineToDelete = ref<Pipeline | null>(null);
const isBatchDeleteMode = ref(false);

const confirmDelete = (pipeline: Pipeline) => {
  pipelineToDelete.value = pipeline;
  isBatchDeleteMode.value = false;
  isDeleteDialogOpen.value = true;
};

const batchDelete = () => {
  isBatchDeleteMode.value = true;
  isDeleteDialogOpen.value = true;
};

const executeDelete = async () => {
  try {
    if (isBatchDeleteMode.value) {
      await Promise.all(selectedIds.value.map(id => pipelineStore.deletePipeline(id)));
      selectedIds.value = [];
      toast({ title: '批量删除成功', description: '选中流水线已移除' });
    } else if (pipelineToDelete.value) {
      await pipelineStore.deletePipeline(pipelineToDelete.value.id);
      toast({ title: '删除成功', description: '流水线已移除' });
    }
  } catch (e) {
    toast({ title: '删除失败', description: '无法移除流水线', variant: 'destructive' });
  } finally {
    isDeleteDialogOpen.value = false;
    pipelineToDelete.value = null;
  }
};

// Helpers
const formatDate = (iso: string) => iso ? dayjs(iso).format('YYYY-MM-DD HH:mm') : '-';
const formatTimeAgo = (iso?: string) => iso ? dayjs(iso).fromNow() : '从未运行';

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    [PipelineStatus.RUNNING]: '运行中',
    [PipelineStatus.STOPPED]: '已停止',
    [PipelineStatus.CREATED]: '已创建',
    [PipelineStatus.FAILED]: '失败'
  };
  return map[status] || status;
};

const getStatusColor = (status: string) => {
  switch(status) {
    case PipelineStatus.RUNNING: return 'bg-green-500';
    case PipelineStatus.STOPPED: return 'bg-amber-500';
    case PipelineStatus.CREATED: return 'bg-blue-500';
    case PipelineStatus.FAILED: return 'bg-red-500';
    default: return 'bg-gray-500';
  }
};

const getStatusBadgeVariant = (status: string) => {
  switch(status) {
    case PipelineStatus.RUNNING: return 'outline'; 
    case PipelineStatus.STOPPED: return 'secondary';
    case PipelineStatus.CREATED: return 'default';
    case PipelineStatus.FAILED: return 'destructive';
    default: return 'outline';
  }
};

</script>
