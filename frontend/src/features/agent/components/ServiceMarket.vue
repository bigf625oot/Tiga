<template>
  <div class="h-full flex bg-background overflow-hidden">
    <!-- Categories Sidebar -->
    <div 
      class="bg-card border-r flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20"
      :class="isSidebarCollapsed ? 'w-[60px]' : 'w-64'"
    >
      <!-- Sidebar Header -->
      <div class="p-4 flex items-center justify-between border-b h-16">
        <div class="flex items-center gap-3 overflow-hidden whitespace-nowrap" :class="{'opacity-0 w-0': isSidebarCollapsed}">
          <div class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary shadow-sm flex-shrink-0">
            <LayoutGrid class="w-4 h-4" />
          </div>
          <span class="font-semibold tracking-tight">分类导航</span>
        </div>
        
        <Button 
          variant="ghost" 
          size="icon" 
          class="h-8 w-8 ml-auto text-muted-foreground"
          @click="isSidebarCollapsed = !isSidebarCollapsed"
          :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
        >
          <ChevronLeft v-if="!isSidebarCollapsed" class="w-4 h-4" />
          <ChevronRight v-else class="w-4 h-4" />
        </Button>
      </div>

      <!-- Categories List -->
      <div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
        <Button
          v-for="item in menuItems" 
          :key="item.id"
          :variant="activeCategory === item.id ? 'secondary' : 'ghost'"
          class="w-full justify-start gap-3 px-3 relative"
          :class="{'justify-center px-0': isSidebarCollapsed}"
          @click="activeCategory = item.id"
          :title="isSidebarCollapsed ? item.label : ''"
        >
          <component :is="getCategoryIcon(item.id)" class="w-4 h-4 flex-shrink-0" />
          
          <span 
            class="truncate transition-all duration-300"
            :class="isSidebarCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'"
          >
            {{ item.label }}
          </span>
          
          <Badge 
            v-if="item.count && !isSidebarCollapsed" 
            variant="secondary" 
            class="ml-auto text-[10px] h-5 px-1.5"
          >
            {{ item.count }}
          </Badge>
        </Button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative bg-muted/10">
      <!-- Header Area -->
      <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold tracking-tight">工具市场</h2>
          <div class="h-4 w-px bg-border"></div>
          <p class="text-xs text-muted-foreground m-0">
            发现、集成和管理您的 AI 助手工具、插件与技能，构建强大的工作流。
          </p>
        </div>
      </div>

      <!-- Search & Filter Bar -->
      <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 border-b bg-background/50">
        <!-- Search -->
        <div class="relative w-full md:w-72">
           <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
           <Input 
             v-model="searchQuery"
             type="text" 
             placeholder="搜索工具、插件或技能..." 
             class="pl-9 h-9 bg-background"
           />
        </div>
        
        <!-- Filters & Actions -->
        <div class="flex items-center gap-3 w-full md:w-auto justify-end">
            <!-- Install Status Filter -->
            <Tabs v-model="installStatus" class="mr-2">
              <TabsList class="h-9">
                <TabsTrigger value="all" class="text-xs h-7 px-3">全部</TabsTrigger>
                <TabsTrigger value="installed" class="text-xs h-7 px-3">已获取</TabsTrigger>
                <TabsTrigger value="uninstalled" class="text-xs h-7 px-3">未获取</TabsTrigger>
              </TabsList>
            </Tabs>

             <div class="flex items-center gap-1 hidden md:flex border-r pr-4 mr-2 h-6">
              <Button 
                v-for="tag in [{id: 'all', label: '全部'}, {id: 'hot', label: '热门'}, {id: 'new', label: '最新'}, {id: 'official', label: '官方'}]" 
                :key="tag.id"
                :variant="activeFilter === tag.id ? 'secondary' : 'ghost'"
                size="sm"
                class="h-7 text-xs px-2.5"
                @click="activeFilter = tag.id"
              >
                {{ tag.label }}
              </Button>
            </div>

            <Button variant="ghost" size="icon" @click="refreshData" :disabled="isLoading" class="h-9 w-9">
              <RefreshCw class="w-4 h-4" :class="{'animate-spin': isLoading}" />
            </Button>

            <Button @click="showCreateToolModal = true" class="shadow-sm gap-2 h-9" size="sm">
              <Plus class="w-3.5 h-3.5" />
              <span>添加工具</span>
            </Button>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar">
        <!-- Skeleton Loader -->
        <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
        <div v-else-if="filteredItems.length === 0" class="flex flex-col items-center justify-center h-[50vh] text-muted-foreground animate-in fade-in duration-500">
          <div class="w-24 h-24 bg-muted/50 rounded-full flex items-center justify-center mb-6">
            <Search class="w-10 h-10 opacity-40" />
          </div>
          <h3 class="text-xl font-semibold text-foreground mb-2">未找到相关服务</h3>
          <p class="text-sm max-w-sm text-center leading-relaxed mb-8 text-muted-foreground">
            我们找不到与您搜索条件匹配的工具。请尝试调整关键词或筛选条件，或者创建一个新工具。
          </p>
          <div class="flex gap-4">
            <Button variant="outline" @click="searchQuery = ''; activeFilter = 'all'">
              清除筛选
            </Button>
            <Button @click="showCreateToolModal = true">
              <Plus class="w-4 h-4 mr-2" />
              创建工具
            </Button>
          </div>
        </div>

        <!-- Tool Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-20 animate-in fade-in zoom-in duration-300">
          <ToolCard 
            v-for="item in filteredItems" 
            :key="item.id" 
            :item="item"
            @edit="openEditModal"
            @delete="deleteTool"
            @install="handleInstall"
          />
        </div>
      </div>
    </div>
  </div>

  <!-- Create/Edit Tool Modal -->
  <Dialog :open="showCreateToolModal" @update:open="(val) => !val && closeModal()">
    <DialogContent class="sm:max-w-[640px] max-h-[90vh] flex flex-col p-0 gap-0 overflow-hidden">
      <DialogHeader class="px-6 py-6 border-b bg-muted/5">
        <DialogTitle class="text-xl">{{ isEditing ? '编辑工具' : '创建新工具' }}</DialogTitle>
        <DialogDescription class="mt-1.5">
          {{ isEditing ? '修改已有的 AI 助手工具配置信息。' : '配置并发布你的 AI 助手工具，使其可被智能体调用。' }}
        </DialogDescription>
      </DialogHeader>
      
      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div class="space-y-8">
          <!-- Tool Type Selection -->
          <div class="space-y-4">
            <Label class="text-base font-medium">工具类型</Label>
            <div class="grid grid-cols-2 gap-4">
              <div 
                @click="newToolForm.type = 'skill'"
                class="relative p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-4 hover:border-primary/50 hover:bg-muted/50"
                :class="newToolForm.type === 'skill' ? 'border-primary bg-primary/5' : 'border-muted'"
              >
                <div class="p-2.5 rounded-lg bg-background border shadow-sm" :class="newToolForm.type === 'skill' ? 'text-primary' : 'text-muted-foreground'">
                  <Zap class="w-5 h-5" />
                </div>
                <div>
                  <div class="font-semibold text-sm">Agent Skill</div>
                  <div class="text-xs text-muted-foreground mt-1.5 leading-relaxed">基于自然语言指令的轻量级技能，易于定义和修改。</div>
                </div>
                <div v-if="newToolForm.type === 'skill'" class="absolute top-3 right-3 w-5 h-5 bg-primary text-primary-foreground rounded-full flex items-center justify-center">
                  <Check class="w-3 h-3" />
                </div>
              </div>

              <div 
                @click="newToolForm.type = 'mcp'"
                class="relative p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-4 hover:border-primary/50 hover:bg-muted/50"
                :class="newToolForm.type === 'mcp' ? 'border-primary bg-primary/5' : 'border-muted'"
              >
                <div class="p-2.5 rounded-lg bg-background border shadow-sm" :class="newToolForm.type === 'mcp' ? 'text-primary' : 'text-muted-foreground'">
                  <Layers class="w-5 h-5" />
                </div>
                <div>
                  <div class="font-semibold text-sm">MCP Server</div>
                  <div class="text-xs text-muted-foreground mt-1.5 leading-relaxed">标准化的模型上下文协议服务，支持更复杂的集成。</div>
                </div>
                <div v-if="newToolForm.type === 'mcp'" class="absolute top-3 right-3 w-5 h-5 bg-primary text-primary-foreground rounded-full flex items-center justify-center">
                  <Check class="w-3 h-3" />
                </div>
              </div>
            </div>
          </div>

          <Separator />

          <!-- Basic Info Grid -->
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-2.5">
              <Label>名称 <span class="text-destructive">*</span></Label>
              <Input v-model="newToolForm.name" placeholder="例如：codemap" class="bg-background" />
            </div>
            <div class="space-y-2.5">
              <Label>版本 <span class="text-destructive">*</span></Label>
              <Input v-model="newToolForm.version" placeholder="1.0.0" class="bg-background" />
            </div>
          </div>

          <!-- Category or MCP Type -->
          <div class="grid gap-6" :class="newToolForm.type === 'mcp' ? 'grid-cols-2' : 'grid-cols-1'">
            <div v-if="newToolForm.type === 'mcp'" class="space-y-2.5">
              <Label>MCP 类型</Label>
              <Select v-model="newToolForm.mcp_type">
                <SelectTrigger class="bg-background">
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stdio">STDIO (Standard Input/Output)</SelectItem>
                  <SelectItem value="sse">SSE (Server-Sent Events)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2.5">
              <Label>分类</Label>
              <Select v-model="newToolForm.category">
                <SelectTrigger class="bg-background">
                  <SelectValue placeholder="选择分类..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="cat in menuItems.filter(c => c.id !== 'all')" :key="cat.id" :value="cat.id">
                    {{ cat.label }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <!-- Description -->
          <div class="space-y-2.5">
            <Label>描述</Label>
            <textarea 
              v-model="newToolForm.description" 
              rows="3" 
              placeholder="简要描述该工具的功能、用途及特点..." 
              class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
            ></textarea>
          </div>

          <!-- Skill Specific: File Upload & Instructions -->
          <div v-if="newToolForm.type === 'skill'" class="space-y-6">
            <div class="space-y-2.5">
              <Label>导入配置 (可选)</Label>
              <div class="group bg-muted/30 border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary hover:bg-primary/5 transition-all cursor-pointer relative">
                <input type="file" @change="handleFileUpload" accept=".zip,.skill" class="absolute inset-0 opacity-0 cursor-pointer z-10" />
                <div class="space-y-3 pointer-events-none">
                  <div class="w-12 h-12 mx-auto rounded-full bg-muted group-hover:bg-primary/10 group-hover:text-primary flex items-center justify-center transition-colors text-muted-foreground">
                    <Upload class="w-6 h-6" />
                  </div>
                  <div class="text-sm text-foreground">
                    <span class="font-semibold text-primary">点击上传</span> 或将文件拖拽到此处
                  </div>
                  <p class="text-xs text-muted-foreground">支持 .zip 或 .skill 格式文件</p>
                </div>
              </div>
            </div>

            <div class="space-y-2.5">
              <Label>指令内容 <span class="text-destructive">*</span></Label>
              <div class="relative">
                <textarea 
                  v-model="newToolForm.content" 
                  rows="8" 
                  placeholder="当这个 Skill 被触发时，你希望模型遵循哪些规则或信息..." 
                  class="flex min-h-[200px] w-full rounded-md border border-input bg-muted/30 px-4 py-3 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                ></textarea>
                <Badge variant="outline" class="absolute right-3 top-3 text-[10px] bg-background/80 backdrop-blur">Markdown</Badge>
              </div>
            </div>
          </div>

          <!-- MCP Specific: Config -->
          <div v-else class="space-y-2.5">
            <Label>MCP 配置 <span class="text-destructive">*</span></Label>
            <div class="relative">
              <textarea 
                v-model="newToolForm.mcp_config" 
                rows="8" 
                class="flex min-h-[200px] w-full rounded-md border border-input bg-slate-950 text-slate-50 px-4 py-3 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                spellcheck="false"
              ></textarea>
              <Badge variant="outline" class="absolute right-3 top-3 text-[10px] bg-slate-900 text-slate-400 border-slate-800">JSON</Badge>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter class="px-6 py-4 border-t bg-muted/5">
        <Button variant="outline" @click="closeModal">取消</Button>
        <Button @click="createTool" :disabled="isSubmitting">
          <Loader2 v-if="isSubmitting" class="mr-2 h-4 w-4 animate-spin" />
          {{ isSubmitting ? '处理中...' : (isEditing ? '保存修改' : '确认创建') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue';
import JSZip from 'jszip';
import ToolCard from './ToolCard.vue';
import { 
  Search, 
  LayoutGrid, 
  RefreshCw, 
  Plus, 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Filter, 
  Layers, 
  Settings, 
  Zap,
  Loader2,
  FileText,
  Upload,
  Check
} from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/components/ui/toast/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

const { toast } = useToast();
const menuItems = ref([]);
const activeCategory = ref('all');
const isSidebarCollapsed = ref(false);
const searchQuery = ref('');
const activeFilter = ref('all');
const installStatus = ref('all');
const isLoading = ref(false);
const showCreateToolModal = ref(false);
const isEditing = ref(false);
const editingId = ref(null);
const installedTools = ref(new Set());
const mcpItems = ref([]);
const skills = ref([]);
const isSubmitting = ref(false);

const getCategoryIcon = (id) => {
  switch (id) {
    case 'all': return LayoutGrid;
    case 'mcp': return Layers;
    case 'skills': return Zap;
    default: return Settings;
  }
};

// ... (Logic remains mostly the same, just removing activeMenuId)

const getStoredInstalled = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem('installed_tools') || '[]'));
  } catch {
    return new Set();
  }
};

installedTools.value = getStoredInstalled();

const handleInstall = async (item) => {
  if (item.installed || item.isInstalling) return;
  item.isInstalling = true;
  await new Promise(resolve => setTimeout(resolve, 800));
  item.installed = true;
  item.isInstalling = false;
  installedTools.value.add(item.id);
  localStorage.setItem('installed_tools', JSON.stringify([...installedTools.value]));
  toast({ title: "安装成功", description: `${item.name} 已成功添加到您的工具库。` });
};

const newToolForm = reactive({
  name: '',
  type: 'skill',
  scope: 'global',
  version: '1.0.0',
  description: '',
  content: '',
  mcp_type: 'stdio',
  mcp_config: '{\n  "command": "python",\n  "args": ["server.py"]\n}',
  category: ''
});

const closeModal = () => {
  showCreateToolModal.value = false;
  setTimeout(() => resetForm(), 200);
};

const resetForm = () => {
  isEditing.value = false;
  editingId.value = null;
  newToolForm.name = '';
  newToolForm.type = 'skill';
  newToolForm.version = '1.0.0';
  newToolForm.description = '';
  newToolForm.content = '';
  newToolForm.mcp_type = 'stdio';
  newToolForm.mcp_config = '{\n  "command": "python",\n  "args": ["server.py"]\n}';
  newToolForm.category = '';
};

const openEditModal = (item) => {
  isEditing.value = true;
  editingId.value = item.id;
  newToolForm.type = item.type;
  newToolForm.name = item.name;
  newToolForm.version = item.version || '1.0.0';
  newToolForm.description = item.description || '';
  newToolForm.category = item.category || '';
  
  if (item.type === 'skill') {
    newToolForm.content = item.content || '';
    newToolForm.scope = item.meta_data?.scope || 'global';
  } else {
    newToolForm.mcp_type = item.mcp_type || 'stdio';
    newToolForm.mcp_config = JSON.stringify(item.config || {}, null, 2);
  }
  showCreateToolModal.value = true;
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  event.target.value = '';

  if (!file.name.endsWith('.zip') && !file.name.endsWith('.skill')) {
    toast({ variant: "destructive", title: "格式错误", description: "不支持的文件格式，请上传 .zip 或 .skill 文件" });
    return;
  }

  try {
    const zip = await JSZip.loadAsync(file);
    const files = Object.keys(zip.files);
    const findFile = (pattern) => {
      const matches = files.filter(path => pattern.test(path) && !zip.files[path].dir);
      if (matches.length === 0) return null;
      matches.sort((a, b) => {
        const depthA = (a.match(/\//g) || []).length;
        const depthB = (b.match(/\//g) || []).length;
        if (depthA !== depthB) return depthA - depthB;
        return a.length - b.length;
      });
      return matches[0];
    };

    const skillMdPath = findFile(/(^|\/)skill\.md$/i);
    if (skillMdPath) {
      const content = await zip.file(skillMdPath).async("string");
      newToolForm.content = content;
      toast({ title: "导入成功", description: `已加载 ${skillMdPath}` });
    } else {
      toast({ variant: "destructive", title: "导入失败", description: "在压缩包中未找到 SKILL.md 文件。" });
    }
    
    const manifestPath = findFile(/(^|\/)(manifest\.json|package\.json)$/i);
    if (manifestPath) {
      try {
        const manifestStr = await zip.file(manifestPath).async("string");
        const manifest = JSON.parse(manifestStr);
        if (manifest.name) newToolForm.name = manifest.name;
        if (manifest.version) newToolForm.version = manifest.version;
        if (manifest.description) newToolForm.description = manifest.description;
      } catch (e) { console.warn("Failed to parse manifest", e); }
    }
  } catch (e) {
    console.error("Error reading file", e);
    toast({ variant: "destructive", title: "解析失败", description: "解析文件失败，请确认文件格式正确且未损坏" });
  }
};

const fetchCategories = async () => {
  try {
    const res = await fetch('/api/v1/service-categories/');
    if (res.ok) {
      const data = await res.json();
      menuItems.value = [{ id: 'all', label: '全部推荐' }, ...data.map(d => ({ id: d.slug, label: d.label }))];
      if (!activeCategory.value) activeCategory.value = 'all';
    }
  } catch (e) { console.error("Failed to fetch categories", e); }
};

const buildQueryParams = () => {
  const params = new URLSearchParams();
  if (searchQuery.value) params.append('q', searchQuery.value);
  if (activeCategory.value && activeCategory.value !== 'all' && activeCategory.value !== 'mcp' && activeCategory.value !== 'skills') {
    params.append('category', activeCategory.value);
  }
  if (activeFilter.value !== 'all') {
    params.append('filter', activeFilter.value);
  }
  return params.toString();
};

const fetchMcpServers = async () => {
  if (activeCategory.value === 'skills') {
    mcpItems.value = [];
    return;
  }
  try {
    const query = buildQueryParams();
    const res = await fetch(`/api/v1/mcp/?${query}`);
    if (res.ok) {
      const data = await res.json();
      mcpItems.value = data.map(item => ({
        ...item,
        type: 'mcp',
        mcp_type: item.type,
        author: item.author || 'User Configured',
        // iconUrl: '/tools/mcp.svg', // Removed to use Lucide icons in ToolCard
        installed: installedTools.value.has(item.id),
        downloads: item.downloads || 0,
        is_official: item.is_official
      }));
    }
  } catch (e) { console.error("Failed to fetch MCP servers", e); }
};

const fetchSkills = async () => {
  if (activeCategory.value === 'mcp') {
    skills.value = [];
    return;
  }
  try {
    const query = buildQueryParams();
    const res = await fetch(`/api/v1/skills/?${query}`);
    if (res.ok) {
      const data = await res.json();
      skills.value = data.map(s => ({
        ...s,
        type: 'skill',
        author: s.author || 'System', 
        // iconUrl: '/tools/skill.svg', // Removed to use Lucide icons in ToolCard
        installed: installedTools.value.has(s.id),
        downloads: s.downloads || 0,
        is_official: s.is_official
      }));
    }
  } catch (e) { console.error("Failed to fetch skills", e); }
};

const refreshData = async () => {
  isLoading.value = true;
  await Promise.all([fetchSkills(), fetchMcpServers()]);
  isLoading.value = false;
};

watch([activeCategory, activeFilter], () => refreshData());

let searchTimeout;
watch(searchQuery, () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => refreshData(), 500);
});

const createTool = async () => {
  if (!newToolForm.name || !newToolForm.version) {
    toast({ variant: "destructive", title: "信息不完整", description: "请完善必要信息" });
    return;
  }
  if (newToolForm.type === 'skill' && !newToolForm.content) {
    toast({ variant: "destructive", title: "信息不完整", description: "请输入技能指令内容" });
    return;
  }

  isSubmitting.value = true;
  try {
    let url = '';
    let body = {};
    const common = {
      name: newToolForm.name,
      description: newToolForm.description,
      category: newToolForm.category
    };
    
    if (newToolForm.type === 'skill') {
      url = isEditing.value ? `/api/v1/skills/${editingId.value}` : '/api/v1/skills/';
      body = { ...common, version: newToolForm.version, content: newToolForm.content, is_active: true, meta_data: { scope: newToolForm.scope } };
    } else {
      url = isEditing.value ? `/api/v1/mcp/${editingId.value}` : '/api/v1/mcp/';
      let config = {};
      try { config = JSON.parse(newToolForm.mcp_config); } catch (e) { 
        toast({ variant: "destructive", title: "JSON 格式错误", description: "MCP 配置必须是有效的 JSON 格式" });
        isSubmitting.value = false; 
        return; 
      }
      body = { ...common, type: newToolForm.mcp_type, config: config, version: newToolForm.version, is_active: true };
    }
    
    const res = await fetch(url, {
      method: isEditing.value ? 'PUT' : 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    
    if (res.ok) {
      closeModal();
      refreshData();
      toast({ title: isEditing.value ? "更新成功" : "创建成功", description: `${newToolForm.name} 已${isEditing.value ? '更新' : '创建'}。` });
    } else {
      const err = await res.json();
      toast({ variant: "destructive", title: "操作失败", description: err.detail || 'Failed to save' });
    }
  } catch (e) { 
    console.error(e); 
    toast({ variant: "destructive", title: "网络错误", description: "无法连接到服务器" });
  } 
  finally { isSubmitting.value = false; }
};

const deleteTool = async (item) => {
  if (!confirm(`Are you sure you want to delete ${item.name}?`)) return;
  try {
    const url = item.type === 'skill' ? `/api/v1/skills/${item.id}` : `/api/v1/mcp/${item.id}`;
    const res = await fetch(url, { method: 'DELETE' });
    if (res.ok) {
      refreshData();
      toast({ title: "删除成功", description: `${item.name} 已被移除。` });
    }
    else {
      toast({ variant: "destructive", title: "删除失败", description: "无法删除该工具。" });
    }
  } catch (e) { 
    console.error(e); 
    toast({ variant: "destructive", title: "网络错误", description: "无法连接到服务器" });
  }
};

const filteredItems = computed(() => {
  let items = [...mcpItems.value, ...skills.value];
  
  if (installStatus.value === 'installed') {
    items = items.filter(item => item.installed);
  } else if (installStatus.value === 'uninstalled') {
    items = items.filter(item => !item.installed);
  }
  
  return items;
});

onMounted(async () => {
  await fetchCategories();
  refreshData();
});
</script>
