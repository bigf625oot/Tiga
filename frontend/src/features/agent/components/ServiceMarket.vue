<template>
  <div class="h-full flex bg-muted/20 overflow-hidden">
    <!-- Collapsible Sidebar -->
    <div 
      class="bg-background border-r flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20"
      :class="isSidebarCollapsed ? 'w-[60px]' : 'w-64'"
    >
      <!-- Sidebar Header -->
      <div class="p-4 flex items-center justify-between border-b h-16">
        <div class="flex items-center gap-3 overflow-hidden whitespace-nowrap" :class="{'opacity-0 w-0': isSidebarCollapsed}">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground shadow-sm flex-shrink-0">
            <LayoutGrid class="w-4 h-4" />
          </div>
          <div>
            <h2 class="text-sm font-semibold tracking-tight">工具市场</h2>
            <p class="text-[10px] text-muted-foreground font-medium">Tool Market</p>
          </div>
        </div>
        
        <!-- Toggle Button -->
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

      <!-- Quick Actions -->
      <div class="p-4 border-t" v-if="!isSidebarCollapsed">
        <div class="bg-muted/50 rounded-lg p-4 border border-border/50">
          <h4 class="text-xs font-semibold mb-1 flex items-center gap-1">
            <Zap class="w-3 h-3 text-yellow-500" />
            需要新工具？
          </h4>
          <p class="text-[10px] text-muted-foreground mb-3 leading-relaxed">自定义工具来扩展您的工作流。</p>
          <Button 
            size="sm" 
            variant="outline" 
            class="w-full h-8 text-xs bg-background"
            @click="showCreateToolModal = true"
          >
            <Plus class="w-3.5 h-3.5 mr-1.5" />
            立即创建
          </Button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative">
      <!-- Header -->
      <div class="px-6 py-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b flex items-center justify-between flex-shrink-0 z-10 sticky top-0">
        <div class="flex items-center gap-4 flex-1 max-w-2xl">
          <!-- Search Bar -->
          <div class="relative w-full max-w-sm">
            <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索工具、插件或技能..." 
              class="pl-9 bg-muted/40 border-muted-foreground/20 focus-visible:bg-background transition-colors"
            />
          </div>
          
          <!-- Filter Tags -->
          <div class="flex items-center gap-1 hidden md:flex border-l pl-4 ml-2 h-8">
            <Button 
              v-for="tag in [{id: 'all', label: '全部'}, {id: 'hot', label: '热门'}, {id: 'new', label: '最新'}, {id: 'official', label: '官方'}]" 
              :key="tag.id"
              :variant="activeFilter === tag.id ? 'secondary' : 'ghost'"
              size="sm"
              class="h-8 text-xs px-3"
              @click="activeFilter = tag.id"
            >
              {{ tag.label }}
            </Button>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Refresh Button -->
          <Button variant="ghost" size="icon" @click="refreshData" :disabled="isLoading">
            <RefreshCw class="w-4 h-4" :class="{'animate-spin': isLoading}" />
          </Button>

          <!-- Primary Create Button -->
          <Button 
            @click="showCreateToolModal = true"
            class="hidden sm:flex gap-2 shadow-sm"
          >
            <Plus class="w-4 h-4" />
            <span>添加工具</span>
          </Button>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar">
        <!-- Skeleton Loader -->
        <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div v-for="n in 8" :key="n" class="border rounded-lg p-6 bg-card h-[280px] flex flex-col space-y-4">
            <div class="flex gap-4">
              <Skeleton class="h-12 w-12 rounded-lg" />
              <div class="space-y-2 flex-1">
                <Skeleton class="h-4 w-3/4" />
                <Skeleton class="h-4 w-1/2" />
              </div>
            </div>
            <div class="space-y-2 flex-1">
              <Skeleton class="h-3 w-full" />
              <Skeleton class="h-3 w-5/6" />
            </div>
            <div class="pt-4 border-t flex justify-between">
              <Skeleton class="h-3 w-16" />
              <Skeleton class="h-3 w-12" />
            </div>
            <Skeleton class="h-9 w-full rounded-md" />
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredItems.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-muted-foreground animate-in fade-in duration-500">
          <div class="w-20 h-20 bg-muted rounded-full flex items-center justify-center mb-6">
            <Search class="w-8 h-8 opacity-50" />
          </div>
          <h3 class="text-lg font-semibold text-foreground mb-2">未找到相关服务</h3>
          <p class="text-sm max-w-xs text-center leading-relaxed mb-6">
            尝试调整搜索关键词或筛选条件，也可以创建新的服务。
          </p>
          <Button variant="outline" @click="searchQuery = ''; activeFilter = 'all'">
            清除筛选条件
          </Button>
        </div>

        <!-- Tool Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20 animate-in fade-in zoom-in duration-300">
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
      <DialogHeader class="px-6 py-4 border-b bg-muted/20">
        <DialogTitle>{{ isEditing ? '编辑工具' : '创建新工具' }}</DialogTitle>
        <DialogDescription>
          {{ isEditing ? '修改已有的 AI 助手工具配置' : '配置并发布你的 AI 助手工具' }}
        </DialogDescription>
      </DialogHeader>
      
      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div class="space-y-6">
          <!-- Tool Type Selection -->
          <div class="space-y-3">
            <Label>工具类型 <span class="text-destructive">*</span></Label>
            <div class="grid grid-cols-2 gap-4">
              <div 
                @click="newToolForm.type = 'skill'"
                class="relative p-4 rounded-lg border-2 cursor-pointer transition-all flex items-start gap-4 hover:bg-muted/50"
                :class="newToolForm.type === 'skill' ? 'border-primary bg-primary/5' : 'border-border'"
              >
                <div class="p-2 rounded-lg" :class="newToolForm.type === 'skill' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'">
                  <Zap class="w-5 h-5" />
                </div>
                <div>
                  <div class="font-medium text-sm">Agent Skill</div>
                  <div class="text-xs text-muted-foreground mt-1 leading-relaxed">基于自然语言指令的轻量级技能。</div>
                </div>
                <Check v-if="newToolForm.type === 'skill'" class="absolute top-3 right-3 w-4 h-4 text-primary" />
              </div>

              <div 
                @click="newToolForm.type = 'mcp'"
                class="relative p-4 rounded-lg border-2 cursor-pointer transition-all flex items-start gap-4 hover:bg-muted/50"
                :class="newToolForm.type === 'mcp' ? 'border-primary bg-primary/5' : 'border-border'"
              >
                <div class="p-2 rounded-lg" :class="newToolForm.type === 'mcp' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'">
                  <Layers class="w-5 h-5" />
                </div>
                <div>
                  <div class="font-medium text-sm">MCP Server</div>
                  <div class="text-xs text-muted-foreground mt-1 leading-relaxed">标准化的模型上下文协议服务。</div>
                </div>
                <Check v-if="newToolForm.type === 'mcp'" class="absolute top-3 right-3 w-4 h-4 text-primary" />
              </div>
            </div>
          </div>

          <!-- Basic Info Grid -->
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-2">
              <Label>名称 <span class="text-destructive">*</span></Label>
              <Input v-model="newToolForm.name" placeholder="例如：codemap" />
            </div>
            <div class="space-y-2">
              <Label>版本 <span class="text-destructive">*</span></Label>
              <Input v-model="newToolForm.version" placeholder="1.0.0" />
            </div>
          </div>

          <!-- Category or MCP Type -->
          <div class="grid gap-6" :class="newToolForm.type === 'mcp' ? 'grid-cols-2' : 'grid-cols-1'">
            <div v-if="newToolForm.type === 'mcp'" class="space-y-2">
              <Label>MCP 类型</Label>
              <Select v-model="newToolForm.mcp_type">
                <SelectTrigger>
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stdio">STDIO (Standard Input/Output)</SelectItem>
                  <SelectItem value="sse">SSE (Server-Sent Events)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <Label>分类</Label>
              <Select v-model="newToolForm.category">
                <SelectTrigger>
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
          <div class="space-y-2">
            <Label>描述</Label>
            <textarea 
              v-model="newToolForm.description" 
              rows="3" 
              placeholder="简要描述该工具的功能、用途及特点..." 
              class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
            ></textarea>
          </div>

          <!-- Skill Specific: File Upload & Instructions -->
          <div v-if="newToolForm.type === 'skill'" class="space-y-5">
            <div class="space-y-2">
              <Label>导入配置 (可选)</Label>
              <div class="group bg-muted/30 border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary hover:bg-primary/5 transition-all cursor-pointer relative">
                <input type="file" @change="handleFileUpload" accept=".zip,.skill" class="absolute inset-0 opacity-0 cursor-pointer z-10" />
                <div class="space-y-3 pointer-events-none">
                  <div class="w-10 h-10 mx-auto rounded-full bg-muted group-hover:bg-primary/10 group-hover:text-primary flex items-center justify-center transition-colors text-muted-foreground">
                    <Upload class="w-5 h-5" />
                  </div>
                  <div class="text-sm text-foreground">
                    <span class="font-semibold text-primary">点击上传</span> 或将文件拖拽到此处
                  </div>
                  <p class="text-xs text-muted-foreground">支持 .zip 或 .skill 格式文件</p>
                </div>
              </div>
            </div>

            <div class="space-y-2">
              <Label>指令内容 <span class="text-destructive">*</span></Label>
              <div class="relative">
                <textarea 
                  v-model="newToolForm.content" 
                  rows="8" 
                  placeholder="当这个 Skill 被触发时，你希望模型遵循哪些规则或信息..." 
                  class="flex min-h-[160px] w-full rounded-md border border-input bg-muted/30 px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                ></textarea>
                <Badge variant="outline" class="absolute right-3 top-3 text-[10px] bg-background/80 backdrop-blur">Markdown</Badge>
              </div>
            </div>
          </div>

          <!-- MCP Specific: Config -->
          <div v-else class="space-y-2">
            <Label>MCP 配置 <span class="text-destructive">*</span></Label>
            <div class="relative">
              <textarea 
                v-model="newToolForm.mcp_config" 
                rows="6" 
                class="flex min-h-[120px] w-full rounded-md border border-input bg-slate-950 text-slate-50 px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                spellcheck="false"
              ></textarea>
              <Badge variant="outline" class="absolute right-3 top-3 text-[10px] bg-slate-900 text-slate-400 border-slate-800">JSON</Badge>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter class="px-6 py-4 border-t bg-muted/20">
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
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

const menuItems = ref([]);
const activeCategory = ref('all');
const isSidebarCollapsed = ref(false);
const searchQuery = ref('');
const activeFilter = ref('all');
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
    alert("不支持的文件格式，请上传 .zip 或 .skill 文件");
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
      alert(`配置导入成功！已加载 ${skillMdPath}`);
    } else {
      alert("在压缩包中未找到 SKILL.md 文件。");
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
    alert("解析文件失败，请确认文件格式正确且未损坏");
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
        iconUrl: '/tools/mcp.svg',
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
        iconUrl: '/tools/skill.svg',
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
    alert("请完善必要信息");
    return;
  }
  if (newToolForm.type === 'skill' && !newToolForm.content) {
    alert("请输入技能指令内容");
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
      try { config = JSON.parse(newToolForm.mcp_config); } catch (e) { alert("Invalid JSON"); isSubmitting.value = false; return; }
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
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Failed to save'}`);
    }
  } catch (e) { console.error(e); alert("Network Error"); } 
  finally { isSubmitting.value = false; }
};

const deleteTool = async (item) => {
  if (!confirm(`Are you sure you want to delete ${item.name}?`)) return;
  try {
    const url = item.type === 'skill' ? `/api/v1/skills/${item.id}` : `/api/v1/mcp/${item.id}`;
    const res = await fetch(url, { method: 'DELETE' });
    if (res.ok) refreshData();
    else alert("Failed to delete");
  } catch (e) { console.error(e); alert("Network Error"); }
};

const filteredItems = computed(() => [...mcpItems.value, ...skills.value]);

onMounted(async () => {
  await fetchCategories();
  refreshData();
});
</script>
