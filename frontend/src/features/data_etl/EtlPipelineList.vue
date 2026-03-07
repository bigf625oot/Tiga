<template>
  <div class="h-full w-full flex flex-col bg-background text-foreground transition-colors duration-300">
    <!-- Header -->
    <div class="px-8 p-6 flex items-center justify-between border-b bg-card">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">ETL 流水线管理</h1>
        <p class="text-sm text-muted-foreground mt-1">管理和监控所有数据处理流程</p>
      </div>
      <div class="flex items-center gap-4">
        <Button @click="emit('create')" class="shadow-sm">
          <Plus class="w-4 h-4 mr-2" />
          新建流水线
        </Button>
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
            class="p-10"
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
            <DropdownMenuItem @click="filterStatus = 'paused'">已暂停</DropdownMenuItem>
            <DropdownMenuItem @click="filterStatus = 'completed'">已完成</DropdownMenuItem>
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
                <Button variant="ghost" class="-ml-4 h-8 data-[state=open]:bg-accent" @click="toggleSort('lastRunTime')">
                  最近运行
                  <ArrowUpDown class="ml-2 h-4 w-4" v-if="sortBy === 'lastRunTime'" />
                </Button>
              </TableHead>
              <TableHead>成功率</TableHead>
              <TableHead>
                <Button variant="ghost" class="-ml-4 h-8 data-[state=open]:bg-accent" @click="toggleSort('createTime')">
                  创建时间
                  <ArrowUpDown class="ml-2 h-4 w-4" v-if="sortBy === 'createTime'" />
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
                    {{ formatTimeAgo(pipeline.lastRunTime) }}
                  </div>
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-2">
                    <div class="w-16 h-2 bg-secondary rounded-full overflow-hidden">
                      <div 
                        class="h-full rounded-full transition-all"
                        :class="pipeline.stats.successRate >= 90 ? 'bg-green-500' : 'bg-amber-500'"
                        :style="{ width: `${pipeline.stats.successRate}%` }"
                      ></div>
                    </div>
                    <span class="text-sm font-medium font-din">{{ pipeline.stats.successRate }}%</span>
                  </div>
                </TableCell>
                <TableCell>
                  <span class="text-muted-foreground text-sm">{{ formatDate(pipeline.createTime) }}</span>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { message, Modal } from 'ant-design-vue'; // Keep ant design for message/modal as requested? Or replace with shadcn Toast/Dialog?
// User asked to use shadcn/ui components. I should use shadcn Toast if possible, but message/Modal logic is already there. 
// For "Interaction walkthrough", it mentions "Toast". shadcn has Toaster. 
// I will switch to shadcn Toaster later if I can, but let's stick to existing logic for logic parts to minimize breakage, 
// BUT the prompt says "Refactor... using shadcn/ui components". 
// I will use shadcn/ui components for layout. For logic like confirm/toast, I'll try to use shadcn if available or stick to AntD for simplicity if shadcn toast setup is complex in this context.
// Actually, `DataSourceManagement.vue` uses `useToast` from shadcn. I should use that too.
// I will assume `useToast` is available.

import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

import { 
  Plus, Search, Filter, ChevronDown, Trash2, RefreshCw, 
  ArrowUpDown, MoreHorizontal, Pencil, Copy, Play, Pause 
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
import { useToast } from '@/components/ui/toast';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const emit = defineEmits(['create', 'edit']);
const { toast } = useToast();

// Types
interface Pipeline {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  createTime: string;
  lastRunTime: string;
  stats: {
    successRate: number;
    totalRuns: number;
  };
}

// State
const pipelines = ref<Pipeline[]>([]);
const isLoading = ref(true);
const isRefreshing = ref(false);
const searchQuery = ref('');
const filterStatus = ref('');
const sortBy = ref('createTime');
const sortDirection = ref<'asc' | 'desc'>('desc');
const selectedIds = ref<string[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);

// Mock Data Generation
const generatePipelines = (count: number): Pipeline[] => {
  const statuses = ['running', 'paused', 'completed', 'failed'] as const;
  return Array.from({ length: count }).map((_, i) => ({
    id: `pl-${1000 + i}`,
    name: `数据处理流水线 ${i + 1} - ${['每日同步', '实时清洗', '异常检测', '归档任务'][i % 4]}`,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    createTime: dayjs().subtract(Math.floor(Math.random() * 30), 'day').toISOString(),
    lastRunTime: dayjs().subtract(Math.floor(Math.random() * 24), 'hour').toISOString(),
    stats: {
      successRate: Math.floor(Math.random() * 20) + 80,
      totalRuns: Math.floor(Math.random() * 1000)
    }
  }));
};

// Logic
const refreshData = () => {
  isRefreshing.value = true;
  isLoading.value = true;
  setTimeout(() => {
    pipelines.value = generatePipelines(25);
    isLoading.value = false;
    isRefreshing.value = false;
    toast({ title: '刷新成功', description: '数据已更新' });
  }, 800);
};

onMounted(() => {
  refreshData();
});

const filteredPipelines = computed(() => {
  let result = pipelines.value;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(p => p.name.toLowerCase().includes(query) || p.id.toLowerCase().includes(query));
  }

  if (filterStatus.value) {
    result = result.filter(p => p.status === filterStatus.value);
  }

  result = [...result].sort((a, b) => {
    let valA: any = a[sortBy.value as keyof Pipeline];
    let valB: any = b[sortBy.value as keyof Pipeline];
    
    // Handle nested stats if needed, simplified here
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

const togglePipelineStatus = (pipeline: Pipeline) => {
  const newStatus = pipeline.status === 'running' ? 'paused' : 'running';
  pipeline.status = newStatus;
  toast({ 
    title: newStatus === 'running' ? '流水线已启动' : '流水线已暂停',
    description: `流水线 "${pipeline.name}" 状态已更新`
  });
};

const duplicatePipeline = (pipeline: Pipeline) => {
  const newPipeline = {
    ...pipeline,
    id: `pl-${Math.floor(Math.random() * 10000)}`,
    name: `${pipeline.name} (副本)`,
    createTime: dayjs().toISOString(),
    status: 'paused' as const
  };
  pipelines.value.unshift(newPipeline);
  toast({ title: '复制成功', description: '新流水线已创建' });
};

const confirmDelete = (pipeline: Pipeline) => {
  // Use browser confirm for now or implement shadcn Dialog based confirmation
  // To keep it simple and within the file scope without extra component overhead:
  if(confirm(`确定要删除流水线 "${pipeline.name}" 吗？`)) {
     pipelines.value = pipelines.value.filter(p => p.id !== pipeline.id);
     toast({ title: '删除成功', description: '流水线已移除' });
  }
};

const batchDelete = () => {
  if(confirm(`确定要删除选中的 ${selectedIds.value.length} 条流水线吗？`)) {
      pipelines.value = pipelines.value.filter(p => !selectedIds.value.includes(p.id));
      selectedIds.value = [];
      toast({ title: '批量删除成功', description: '选中流水线已移除' });
  }
};

// Helpers
const formatDate = (iso: string) => dayjs(iso).format('YYYY-MM-DD HH:mm');
const formatTimeAgo = (iso: string) => dayjs(iso).fromNow();

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  };
  return map[status] || status;
};

const getStatusColor = (status: string) => {
  switch(status) {
    case 'running': return 'bg-green-500';
    case 'paused': return 'bg-amber-500';
    case 'completed': return 'bg-blue-500';
    case 'failed': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
};

const getStatusBadgeVariant = (status: string) => {
  switch(status) {
    case 'running': return 'outline'; // custom styling usually needed for specific colors if not using default variants
    case 'paused': return 'secondary';
    case 'completed': return 'default';
    case 'failed': return 'destructive';
    default: return 'outline';
  }
};

</script>
