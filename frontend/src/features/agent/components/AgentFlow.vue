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
        </div>
    </div>
    
    <!-- Toolbar -->
    <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
       <!-- Left: Empty placeholder to balance flex layout -->
       <div class="hidden md:block w-full md:w-64"></div>
       
       <!-- Center: View Tabs -->
       <div class="flex items-center justify-center flex-1">
         <Tabs v-model="currentTab" class="w-[200px]" @update:modelValue="handleTabChange">
           <TabsList class="grid w-full grid-cols-2 h-9 bg-muted/80 p-1 rounded-lg border border-border/50 items-center">
             <TabsTrigger value="instances" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">自定义</TabsTrigger>
             <TabsTrigger value="templates" class="text-xs font-medium px-4 h-7 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">模板</TabsTrigger>
           </TabsList>
         </Tabs>
       </div>

       <!-- Right: Actions -->
       <div class="flex items-center gap-3 w-full md:w-auto justify-end">
          <div class="relative w-full md:w-64 group">
             <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
             <Input 
               v-model="searchQuery" 
               placeholder="搜索工作流..." 
               class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50"
               @input="handleSearch"
             />
             <button v-if="searchQuery" @click="searchQuery = ''; handleSearch()"
                 class="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors">
                 <X class="h-4 w-4" />
             </button>
          </div>

          <div class="h-4 w-px bg-border hidden md:block mx-1"></div>
          
          <!-- Filter Select -->
          <Select v-model="filterStatus" @update:modelValue="handleFilter">
             <SelectTrigger class="w-[120px] h-9 bg-background">
                <SelectValue placeholder="筛选状态" />
             </SelectTrigger>
             <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="active">已启用</SelectItem>
                <SelectItem value="inactive">已禁用</SelectItem>
             </SelectContent>
          </Select>

          <Button @click="handleRefresh" variant="outline" size="icon" class="h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95 flex-shrink-0" title="刷新列表">
             <RefreshCw class="h-4 w-4 text-muted-foreground" :class="{ 'animate-spin': store.loading }" />
          </Button>

          <Button size="sm" @click="handleCreate" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2 flex-shrink-0">
             <Plus class="h-3.5 w-3.5" />
             新建流
          </Button>
       </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 flex flex-col">
       <!-- Loading -->
       <div v-if="store.loading && store.workflows.length === 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
         <div v-for="n in 8" :key="n" class="border rounded-xl p-4 bg-card h-[180px] flex flex-col space-y-3 shadow-sm">
           <div class="flex gap-3">
             <Skeleton class="h-10 w-10 rounded-lg" />
             <div class="space-y-2 flex-1 pt-1">
               <Skeleton class="h-4 w-1/2" />
               <Skeleton class="h-3 w-1/4" />
             </div>
           </div>
           <div class="space-y-2 flex-1 pt-2">
             <Skeleton class="h-3 w-full" />
             <Skeleton class="h-3 w-5/6" />
           </div>
           <div class="pt-3 border-t flex justify-between items-center mt-auto">
             <Skeleton class="h-3 w-20" />
             <Skeleton class="h-7 w-16 rounded-md" />
           </div>
         </div>
       </div>

       <!-- Empty State -->
       <div v-else-if="!store.loading && store.workflows.length === 0" class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px] w-full max-w-3xl mx-auto text-muted-foreground animate-in fade-in duration-300">
          <div class="w-24 h-24 bg-muted/50 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
             <Search v-if="searchQuery" class="w-10 h-10 text-muted-foreground/50" />
             <GitBranch v-else class="w-10 h-10 text-muted-foreground/50" />
          </div>
          <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">{{ searchQuery ? '未找到相关工作流' : '暂无智能体流' }}</h3>
          <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">
            {{ searchQuery ? '请尝试调整搜索关键词或筛选条件。' : '当前暂无智能体流，您可以点击下方按钮创建一个新的智能体流。' }}
          </p>
          <Button v-if="!searchQuery && currentTab !== 'templates'" 
              @click="handleCreate"
              class="px-8 shadow-sm hover:scale-105 transition-transform"
          >
            <Plus class="mr-2 h-4 w-4" />
            新建流
          </Button>
       </div>

       <!-- Grid -->
       <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <FlowCard 
            v-for="flow in store.workflows" 
            :key="flow.id" 
            :flow="flow"
            @click="handleEdit(flow.id)"
            @edit="handleEdit(flow.id)"
            @delete="handleDelete(flow.id)"
          >
            <template #actions>
                <DropdownMenuItem v-if="!flow.is_template" @click.stop="saveAsTemplate(flow)">
                    <span class="flex items-center gap-2 w-full">
                        <Copy class="w-4 h-4" /> 保存为模板
                    </span>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="flow.is_template" @click.stop="createFromTemplate(flow)">
                    <span class="flex items-center gap-2 w-full">
                        <Plus class="w-4 h-4" /> 从模板创建
                    </span>
                </DropdownMenuItem>
            </template>
          </FlowCard>
       </div>
    </div>
  </div>

  <!-- Editor View -->
  <AgentFlowEditor v-else @close="handleBack" />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAgentFlowStore } from '../store/agentFlow.store';
import { GitBranch, Plus, Search, Copy, RefreshCw, X } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import AgentFlowEditor from './AgentFlowEditor.vue';
import FlowCard from './FlowCard.vue';
import { useDebounceFn } from '@vueuse/core';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();
const store = useAgentFlowStore();
const emit = defineEmits(['back']); // 声明 back 事件以阻止透传给根节点，防止触发父组件 App.vue 的 handleBack
const isEditing = ref(false);
const searchQuery = ref('');
const filterStatus = ref('all');
const currentTab = ref('instances'); // instances | templates

onMounted(() => {
  store.fetchWorkflows({ is_template: currentTab.value === 'templates' });
});

const handleSearch = useDebounceFn(() => {
   store.fetchWorkflows({ q: searchQuery.value, is_template: currentTab.value === 'templates' });
}, 300);

const handleFilter = () => {
    // Currently backend only supports query.
    // If we want status filtering, we need to implement it in backend or frontend.
    // For now, let's keep it simple or assume backend will ignore unknown params if passed,
    // or we filter client-side if data is small.
    // Let's reload for now.
    store.fetchWorkflows({ q: searchQuery.value, is_template: currentTab.value === 'templates' });
};

const handleTabChange = () => {
    store.fetchWorkflows({ q: searchQuery.value, is_template: currentTab.value === 'templates' });
};

const handleRefresh = () => {
    store.fetchWorkflows({ q: searchQuery.value, is_template: currentTab.value === 'templates' });
};

const handleCreate = () => {
  store.resetCurrentWorkflow();
  // If creating from template tab, maybe we want to set is_template default?
  // But usually create button in main view is for new instances.
  // We can add a toggle in editor later if needed.
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
  store.fetchWorkflows({ is_template: currentTab.value === 'templates' }); // Refresh list
};

const saveAsTemplate = async (flow: any) => {
    const newFlow = {
        name: `${flow.name} (模板)`,
        description: flow.description,
        definition: flow.definition,
        is_template: true
    };
    try {
        await store.createWorkflow(newFlow);
        toast({ title: '保存成功', description: `已将 "${flow.name}" 保存为模板。` });
        if (currentTab.value === 'templates') {
             store.fetchWorkflows({ q: searchQuery.value, is_template: true });
        }
    } catch (e) {
        toast({ variant: 'destructive', title: '保存失败', description: '无法保存为模板。' });
    }
};

const createFromTemplate = async (flow: any) => {
    const newFlow = {
        name: `${flow.name} (副本)`,
        description: flow.description,
        definition: flow.definition,
        is_template: false
    };
    try {
        await store.createWorkflow(newFlow);
        currentTab.value = 'instances';
        store.fetchWorkflows({ q: searchQuery.value, is_template: false });
        toast({ title: '创建成功', description: `已从模板创建 "${newFlow.name}"。` });
    } catch (e) {
        toast({ variant: 'destructive', title: '创建失败', description: '无法从模板创建。' });
    }
};
</script>
