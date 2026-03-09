<template>
  <div class="container mx-auto p-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div class="flex flex-col space-y-2">
      <h1 class="text-3xl font-bold tracking-tight">任务历史</h1>
      <p class="text-muted-foreground">
        查看和管理所有的指标提取与分析任务记录
      </p>
    </div>

    <Card>
      <div class="p-4 flex items-center justify-between gap-4 border-b">
        <div class="flex items-center flex-1 gap-2 max-w-sm">
          <Search class="w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="搜索任务ID或文件名..." 
            v-model="searchQuery"
            class="h-9"
          />
        </div>
        <div class="flex items-center gap-2">
          <Select v-model="statusFilter">
            <SelectTrigger class="w-[120px] h-9">
              <SelectValue placeholder="状态筛选" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="processing">进行中</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
            </SelectContent>
          </Select>
          
          <Select v-model="typeFilter">
            <SelectTrigger class="w-[120px] h-9">
              <SelectValue placeholder="任务类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="batch">批量提取</SelectItem>
              <SelectItem value="single">单条提取</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="icon" class="h-9 w-9" @click="refreshData">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoading }" />
          </Button>
        </div>
      </div>

      <div class="relative w-full overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-[180px]">任务ID</TableHead>
              <TableHead>任务名称/文件</TableHead>
              <TableHead>类型</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>指标数量</TableHead>
              <TableHead>耗时</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead class="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <template v-if="filteredTasks.length > 0">
              <TableRow v-for="task in filteredTasks" :key="task.id" class="group">
                <TableCell class="font-mono text-xs text-muted-foreground">
                  {{ task.id }}
                </TableCell>
                <TableCell class="font-medium">
                  <div class="flex items-center gap-2">
                    <FileText v-if="task.type === 'batch'" class="w-4 h-4 text-blue-500" />
                    <File v-else class="w-4 h-4 text-purple-500" />
                    <span class="truncate max-w-[200px]" :title="task.name">{{ task.name }}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" class="font-normal text-xs">
                    {{ task.type === 'batch' ? '批量提取' : '单条提取' }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-2">
                    <component :is="getStatusIcon(task.status)" class="w-3.5 h-3.5" :class="getStatusColor(task.status)" />
                    <span class="text-sm">{{ getStatusLabel(task.status) }}</span>
                  </div>
                </TableCell>
                <TableCell>
                  {{ task.indicatorCount }}
                </TableCell>
                <TableCell class="text-muted-foreground text-xs font-mono">
                  {{ task.duration }}s
                </TableCell>
                <TableCell class="text-muted-foreground text-xs">
                  {{ task.createdAt }}
                </TableCell>
                <TableCell class="text-right">
                  <div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="icon" class="h-8 w-8" title="查看详情">
                      <Eye class="w-4 h-4" />
                    </Button>
                    <Button v-if="task.status === 'failed'" variant="ghost" size="icon" class="h-8 w-8 text-destructive hover:text-destructive" title="重试任务">
                      <RotateCw class="w-4 h-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            </template>
            <TableRow v-else>
              <TableCell colspan="8" class="h-24 text-center">
                <div class="flex flex-col items-center justify-center text-muted-foreground gap-2">
                  <SearchX class="w-8 h-8 opacity-50" />
                  <p>暂无任务记录</p>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      <div class="p-4 border-t flex items-center justify-between">
        <span class="text-sm text-muted-foreground">
          显示 {{ filteredTasks.length }} 条记录
        </span>
        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" :disabled="currentPage === 1" @click="currentPage--">
            上一页
          </Button>
          <Button variant="outline" size="sm" :disabled="currentPage * pageSize >= totalTasks" @click="currentPage++">
            下一页
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { 
  Search, RefreshCw, FileText, File, Eye, RotateCw, 
  CheckCircle2, XCircle, Clock, AlertCircle, SearchX 
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// Types
interface Task {
  id: string;
  name: string;
  type: 'batch' | 'single';
  status: 'completed' | 'processing' | 'failed' | 'pending';
  indicatorCount: number;
  duration: number;
  createdAt: string;
}

// State
const searchQuery = ref('');
const statusFilter = ref('all');
const typeFilter = ref('all');
const isLoading = ref(false);
const currentPage = ref(1);
const pageSize = 10;
const tasks = ref<Task[]>([]);

// Mock Data Generation
const generateMockTasks = () => {
  const mockTasks: Task[] = [];
  const statuses = ['completed', 'processing', 'failed', 'pending'] as const;
  const types = ['batch', 'single'] as const;

  for (let i = 0; i < 25; i++) {
    const isBatch = Math.random() > 0.6;
    mockTasks.push({
      id: `TASK-${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
      name: isBatch ? `批量提取任务_${20240301 + i}` : `年度财务报告_${i + 1}.pdf`,
      type: isBatch ? 'batch' : 'single',
      status: statuses[Math.floor(Math.random() * statuses.length)],
      indicatorCount: Math.floor(Math.random() * 50) + 5,
      duration: Number((Math.random() * 60 + 5).toFixed(1)),
      createdAt: new Date(Date.now() - Math.random() * 1000000000).toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
      })
    });
  }
  return mockTasks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
};

// Computed
const filteredTasks = computed(() => {
  return tasks.value.filter(task => {
    const matchesSearch = task.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                         task.id.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesStatus = statusFilter.value === 'all' || task.status === statusFilter.value;
    const matchesType = typeFilter.value === 'all' || task.type === typeFilter.value;
    
    return matchesSearch && matchesStatus && matchesType;
  });
});

const totalTasks = computed(() => filteredTasks.value.length);

// Methods
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    completed: '已完成',
    processing: '进行中',
    failed: '失败',
    pending: '等待中'
  };
  return labels[status] || status;
};

const getStatusIcon = (status: string) => {
  const icons: Record<string, any> = {
    completed: CheckCircle2,
    processing: Clock,
    failed: XCircle,
    pending: AlertCircle
  };
  return icons[status];
};

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    completed: 'text-green-500',
    processing: 'text-blue-500 animate-pulse',
    failed: 'text-red-500',
    pending: 'text-amber-500'
  };
  return colors[status];
};

const refreshData = async () => {
  isLoading.value = true;
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 800));
  tasks.value = generateMockTasks();
  isLoading.value = false;
};

// Lifecycle
onMounted(() => {
  refreshData();
});
</script>
