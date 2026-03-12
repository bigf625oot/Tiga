<template>
  <!-- List View -->
  <div v-if="!isEditing" class="h-full flex flex-col bg-background overflow-hidden">
    <!-- Compact Header -->
    <div
        class="px-6 py-4 border-b border-border flex items-center justify-between flex-shrink-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
        <div class="flex items-center gap-3">
            <h2 class="text-lg font-semibold tracking-tight text-foreground">智能体流</h2>
            <div class="h-4 w-px bg-border"></div>
            <p class="text-muted-foreground text-xs truncate max-w-xl">
                构建和管理智能体工作流
            </p>
        </div>

        <div class="flex items-center gap-2">
            <Button size="sm" class="h-9 shadow-sm" @click="handleCreate">
                <Plus class="mr-2 h-4 w-4" />
                新建流
            </Button>
        </div>
    </div>
    
    <!-- Toolbar -->
    <div class="px-6 py-4 flex items-center gap-4 border-b border-border/50 bg-muted/20">
       <div class="relative w-72">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            v-model="searchQuery" 
            placeholder="搜索工作流..." 
            class="pl-9 bg-background"
            @input="handleSearch"
          />
       </div>
       
       <!-- Filter Select -->
       <Select v-model="filterStatus" @update:modelValue="handleFilter">
          <SelectTrigger class="w-[180px] bg-background">
             <SelectValue placeholder="筛选状态" />
          </SelectTrigger>
          <SelectContent>
             <SelectItem value="all">全部状态</SelectItem>
             <SelectItem value="active">已启用</SelectItem>
             <SelectItem value="inactive">已禁用</SelectItem>
          </SelectContent>
       </Select>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6">
       <!-- Loading -->
       <div v-if="store.loading && store.workflows.length === 0" class="flex justify-center py-20">
          <Loader2 class="h-8 w-8 animate-spin text-primary" />
       </div>

       <!-- Empty State -->
       <div v-else-if="!store.loading && store.workflows.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
          <div class="p-4 bg-muted rounded-full inline-block mb-4">
            <GitBranch class="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 class="text-lg font-medium mb-2">暂无智能体流</h3>
          <p class="text-sm text-muted-foreground max-w-sm mx-auto mb-6">
            开始创建一个新的智能体流来自动化您的任务。
          </p>
          <Button @click="handleCreate">
            <Plus class="mr-2 h-4 w-4" />
            新建流
          </Button>
       </div>

       <!-- Grid -->
       <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <Card v-for="flow in store.workflows" :key="flow.id" class="hover:shadow-md transition-shadow cursor-pointer group flex flex-col" @click="handleEdit(flow.id)">
             <CardHeader class="pb-2">
                <div class="flex justify-between items-start">
                   <CardTitle class="text-base truncate pr-2" :title="flow.name">{{ flow.name }}</CardTitle>
                   <DropdownMenu>
                      <DropdownMenuTrigger as-child>
                         <Button variant="ghost" size="icon" class="h-8 w-8 -mr-2 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
                            <MoreHorizontal class="h-4 w-4" />
                         </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                         <DropdownMenuItem @click.stop="handleEdit(flow.id)">编辑</DropdownMenuItem>
                         <DropdownMenuItem @click.stop="handleDelete(flow.id)" class="text-destructive">删除</DropdownMenuItem>
                      </DropdownMenuContent>
                   </DropdownMenu>
                </div>
                <CardDescription class="line-clamp-2 h-10 text-xs mt-1">
                   {{ flow.description || '暂无描述' }}
                </CardDescription>
             </CardHeader>
             <div class="flex-1"></div>
             <CardFooter class="pt-3 pb-3 text-xs text-muted-foreground border-t bg-muted/10 flex justify-between items-center">
                <span>更新于 {{ formatDate(flow.updated_at) }}</span>
                <span v-if="flow.is_active" class="flex items-center gap-1 text-green-600">
                    <span class="h-1.5 w-1.5 rounded-full bg-green-600"></span>
                    已启用
                </span>
                <span v-else class="flex items-center gap-1 text-muted-foreground">
                    <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground"></span>
                    已禁用
                </span>
             </CardFooter>
          </Card>
       </div>
    </div>
  </div>

  <!-- Editor View -->
  <AgentFlowEditor v-else @back="handleBack" />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAgentFlowStore } from '../store/agentFlow.store';
import { GitBranch, Plus, Search, MoreHorizontal, Loader2 } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import AgentFlowEditor from './AgentFlowEditor.vue';
import { useDebounceFn } from '@vueuse/core';
import dayjs from 'dayjs';

const store = useAgentFlowStore();
const isEditing = ref(false);
const searchQuery = ref('');
const filterStatus = ref('all');

onMounted(() => {
  store.fetchWorkflows();
});

const handleSearch = useDebounceFn(() => {
   store.fetchWorkflows({ q: searchQuery.value });
}, 300);

const handleFilter = () => {
    // Currently backend only supports query.
    // If we want status filtering, we need to implement it in backend or frontend.
    // For now, let's keep it simple or assume backend will ignore unknown params if passed,
    // or we filter client-side if data is small.
    // Let's reload for now.
    store.fetchWorkflows({ q: searchQuery.value });
};

const handleCreate = () => {
  store.resetCurrentWorkflow();
  isEditing.value = true;
};

const handleEdit = async (id: string) => {
  await store.loadWorkflow(id);
  isEditing.value = true;
};

const handleDelete = async (id: string) => {
    if (confirm('确定要删除这个工作流吗？')) {
        await store.deleteWorkflow(id);
    }
};

const handleBack = () => {
  isEditing.value = false;
  searchQuery.value = ''; // Reset search query
  store.fetchWorkflows(); // Refresh list
};

const formatDate = (date?: string) => {
    if (!date) return '-';
    return dayjs(date).format('YYYY-MM-DD HH:mm');
};
</script>
