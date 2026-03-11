<template>
  <div class="h-full w-full flex flex-col bg-background text-foreground transition-colors duration-300">
    <!-- Header Banner -->
    <div class="px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">ETL 流水线管理</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-muted-foreground text-xs truncate max-w-xl">
            管理和监控所有数据处理流程
          </p>
        </div>
        <div class="flex items-center gap-2">
           <Button 
            @click="isCreateDialogOpen = true" 
            size="sm"
            class="h-9"
          >
            <Plus class="w-4 h-4 mr-2" />
            新建流水线
          </Button>
        </div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="px-8 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-4 w-full md:w-auto">
        <div class="relative flex-1 md:w-80">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            v-model="searchQuery"
            placeholder="搜索流水线名称..." 
            class="pl-9"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" class="gap-2">
              <Filter class="w-4 h-4" />
              {{ filterStatus ? getStatusLabel(filterStatus) : '所有状态' }}
              <ChevronDown class="w-4 h-4 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem @click="filterStatus = ''">所有状态</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="filterStatus = 'running'">运行中</DropdownMenuItem>
            <DropdownMenuItem @click="filterStatus = 'stopped'">已停止</DropdownMenuItem>
            <DropdownMenuItem @click="filterStatus = 'created'">已创建</DropdownMenuItem>
            <DropdownMenuItem @click="filterStatus = 'failed'">失败</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div class="flex items-center gap-2 w-full md:w-auto justify-end">
        <Button 
          v-if="selectedIds.length > 0"
          variant="destructive"
          size="sm"
          @click="batchDelete"
          class="gap-2"
        >
          <Trash2 class="w-4 h-4" />
          批量删除 ({{ selectedIds.length }})
        </Button>
        
        <Button variant="ghost" size="icon" title="刷新列表" @click="refreshData">
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" />
        </Button>
      </div>
    </div>

    <!-- Data Table -->
    <div class="flex-1 overflow-auto px-8 pb-8">
      <SkeletonETL v-if="isLoading" :rows="10" />
      
      <div v-else class="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-[50px]">
                <Checkbox 
                  :checked="isAllSelected"
                  @update:checked="toggleSelectAll"
                  aria-label="Select all"
                />
              </TableHead>
              <TableHead class="w-[300px]">
                <Button variant="ghost" class="-ml-4 h-8 data-[state=open]:bg-accent" @click="toggleSort('name')">
                  流水线名称
                  <ArrowUpDown class="ml-2 h-4 w-4" v-if="sortBy === 'name'" />
                </Button>
              </TableHead>
              <TableHead>状态</TableHead>
              <TableHead>
                <Button variant="ghost" class="-ml-4 h-8 data-[state=open]:bg-accent" @click="toggleSort('last_run_at')">
                  最近运行
                  <ArrowUpDown class="ml-2 h-4 w-4" v-if="sortBy === 'last_run_at'" />
                </Button>
              </TableHead>
              <TableHead>
                <Button variant="ghost" class="-ml-4 h-8 data-[state=open]:bg-accent" @click="toggleSort('created_at')">
                  创建时间
                  <ArrowUpDown class="ml-2 h-4 w-4" v-if="sortBy === 'created_at'" />
                </Button>
              </TableHead>
              <TableHead class="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <template v-if="paginatedPipelines.length === 0">
              <TableRow>
                <TableCell colspan="7" class="h-24 text-center">
                  <div class="flex flex-col items-center justify-center text-muted-foreground py-8">
                    <Search class="h-8 w-8 mb-2 opacity-50" />
                    <p>暂无符合条件的流水线</p>
                  </div>
                </TableCell>
              </TableRow>
            </template>

            <template v-else>
              <TableRow 
                v-for="pipeline in paginatedPipelines" 
                :key="pipeline.id"
                :data-state="selectedIds.includes(pipeline.id) ? 'selected' : undefined"
              >
                <TableCell>
                  <Checkbox 
                    :checked="selectedIds.includes(pipeline.id)"
                    @update:checked="toggleSelection(pipeline.id)"
                    aria-label="Select row"
                  />
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-4">
                    <div 
                      class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 shadow-sm text-white font-semibold text-sm"
                      :class="getStatusColor(pipeline.status)"
                    >
                      {{ pipeline.name.substring(0,1).toUpperCase() }}
                    </div>
                    <div>
                      <div class="font-medium text-foreground hover:text-primary cursor-pointer transition-colors" @click="emit('edit', pipeline)">
                        {{ pipeline.name }}
                      </div>
                      <div class="text-xs text-muted-foreground font-mono mt-0.5">
                        {{ pipeline.id }}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge :variant="getStatusBadgeVariant(pipeline.status)" class="capitalize">
                    {{ getStatusLabel(pipeline.status) }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div class="text-sm">
                    {{ formatTimeAgo(pipeline.last_run_at) }}
                  </div>
                </TableCell>
                <TableCell>
                  <span class="text-muted-foreground text-sm">{{ formatDate(pipeline.created_at) }}</span>
                </TableCell>
                <TableCell class="text-right">
                  <div class="flex items-center justify-end gap-2">
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      class="h-8 w-8"
                      :title="pipeline.status === 'running' ? '暂停' : '启动'"
                      @click="togglePipelineStatus(pipeline)"
                    >
                      <Pause v-if="pipeline.status === 'running'" class="h-4 w-4 text-amber-500" />
                      <Play v-else class="h-4 w-4 text-green-500" />
                    </Button>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger as-child>
                        <Button variant="ghost" size="icon" class="h-8 w-8">
                          <MoreHorizontal class="h-4 w-4" />
                          <span class="sr-only">Open menu</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem @click="emit('edit', pipeline)">
                          <Pencil class="mr-2 h-4 w-4" /> 编辑
                        </DropdownMenuItem>
                        <DropdownMenuItem @click="duplicatePipeline(pipeline)">
                          <Copy class="mr-2 h-4 w-4" /> 复制
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem @click="confirmDelete(pipeline)" class="text-destructive focus:text-destructive">
                          <Trash2 class="mr-2 h-4 w-4" /> 删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </TableCell>
              </TableRow>
            </template>
          </TableBody>
        </Table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between py-4" v-if="!isLoading && filteredPipelines.length > 0">
        <div class="text-sm text-muted-foreground">
          显示 {{ (currentPage - 1) * pageSize + 1 }} 到 {{ Math.min(currentPage * pageSize, filteredPipelines.length) }} 条，共 {{ filteredPipelines.length }} 条
        </div>
        <div class="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            上一页
          </Button>
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
          <Button
            variant="outline"
            size="sm"
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            下一页
          </Button>
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
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

import { 
  Plus, Search, Filter, ChevronDown, Trash2, RefreshCw, 
  ArrowUpDown, MoreHorizontal, Pencil, Copy, Play, Pause,
  Network, Database, Sparkles, File, FilePlus
} from 'lucide-vue-next';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import { SkeletonETL } from '@/components/skeletons';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
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

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const emit = defineEmits(['create', 'edit']);
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
    let valA: any = a[sortBy.value as keyof Pipeline];
    let valB: any = b[sortBy.value as keyof Pipeline];
    
    if (sortBy.value === 'name') {
       // string compare
    } else {
       // date or number compare
       valA = new Date(valA as string).getTime();
       valB = new Date(valB as string).getTime();
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

const toggleSelection = (id: string) => {
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
const formatTimeAgo = (iso: string) => iso ? dayjs(iso).fromNow() : '从未运行';

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
