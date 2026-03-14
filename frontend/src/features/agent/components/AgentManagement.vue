<template>
    <div class="h-full flex flex-col bg-background overflow-hidden">
        <!-- Header Area (Always visible) -->
        <div class="px-6 py-4 border-b flex justify-between items-center bg-muted/20 flex-shrink-0">
            <div class="flex items-center gap-3">
                <h2 class="text-lg font-semibold tracking-tight">智能体中心</h2>
                <div class="h-4 w-px bg-border"></div>
                <p class="text-xs text-muted-foreground m-0">
                    管理您的智能体助手与应用模版。
                </p>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar bg-muted/10">
            <div class="max-w-[1800px] mx-auto w-full flex flex-col gap-8">

                <Loading v-if="isLoading" type="skeleton-card" />

                <template v-else>
                    <!-- Filter Tabs & Search -->
                    <div class="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-20 bg-background/50 border-b">
                        <div class="relative w-full md:w-72 group">
                            <Search class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                            <Input v-model="searchQuery" @focus="handleSearchFocus" @blur="handleSearchBlur"
                                @input="handleSearchInput" placeholder="搜索智能体..."
                                class="pl-9 h-9 bg-background border-input/80 focus-visible:ring-1 focus-visible:ring-primary/30 pr-8 shadow-sm transition-all hover:border-primary/50" />
                            <button v-if="searchQuery" @click="searchQuery = ''; showSuggestions = false"
                                class="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors">
                                <X class="h-4 w-4" />
                            </button>

                            <!-- Suggestions Dropdown -->
                            <div v-if="showSuggestions && searchSuggestions.length > 0"
                                class="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-50 overflow-hidden">
                                <div v-for="(suggestion, index) in searchSuggestions" :key="index"
                                    @click="selectSuggestion(suggestion)"
                                    class="px-4 py-2 text-sm text-slate-700 hover:bg-muted cursor-pointer flex items-center gap-2">
                                    <Search class="w-3 h-3 text-muted-foreground" />
                                    <span v-html="highlightMatch(suggestion)"></span>
                                </div>
                            </div>
                        </div>

                        <div class="flex items-center gap-3 w-full md:w-auto justify-end">
                            <Tabs :model-value="activeTab" @update:model-value="(val) => activeTab = val" class="w-full md:w-auto">
                                <TabsList class="grid w-full grid-cols-3 h-9 bg-muted/80 p-1 rounded-lg border border-border/50">
                                    <TabsTrigger value="all" class="text-xs font-medium px-4 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">全部</TabsTrigger>
                                    <TabsTrigger value="my-agents" class="text-xs font-medium px-4 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">自定义</TabsTrigger>
                                    <TabsTrigger value="discover" class="text-xs font-medium px-4 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all">模版</TabsTrigger>
                                </TabsList>
                            </Tabs>

                            <Button @click="fetchAgents" variant="outline" size="icon" class="h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95" title="刷新列表">
                                <RefreshCw class="h-4 w-4 text-muted-foreground" :class="{ 'animate-spin': isLoading }" />
                            </Button>

                            <Button @click="openCreateModal" size="sm" class="h-9 px-4 shadow-sm font-medium transition-all hover:scale-105 active:scale-95 gap-2">
                                <Plus class="h-3.5 w-3.5" />
                                创建智能体
                            </Button>
                        </div>
                    </div>

                    <!-- Agent List -->
                    <div class="flex flex-col gap-8">
                        <!-- Search Header -->
                        <div v-if="searchQuery" class="flex items-center gap-2">
                            <h3 class="text-lg font-semibold tracking-tight text-foreground">搜索结果</h3>
                            <span class="text-sm text-muted-foreground">({{ displayedAgents.length }})</span>
                        </div>

                        <div v-if="displayedAgents.length > 0">
                            <!-- Grouped View for 'all' tab -->
                            <template v-if="activeTab === 'all'">
                                <div class="flex flex-col gap-12">
                                    <div v-if="filteredMyAgents.length > 0" class="flex flex-col gap-5">
                                        <h3
                                            class="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2 pl-1">
                                            <div class="w-1.5 h-4 bg-primary rounded-full"></div>
                                            自定义智能体
                                            <span class="text-xs font-normal text-muted-foreground/70 ml-1">({{
                                                filteredMyAgents.length }})</span>
                                        </h3>
                                        <div
                                            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 animate-fade-in">
                                            <AgentCard v-for="agent in filteredMyAgents" :key="agent.id" 
                                                :agent="agent"
                                                :selected="currentAgent?.id === agent.id"
                                                @click="handleAgentClick" @edit="editAgent" @delete="deleteAgent" />
                                        </div>
                                    </div>

                                    <div v-if="filteredDiscoverAgents.length > 0" class="flex flex-col gap-5">
                                        <h3
                                            class="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2 pl-1">
                                            <div class="w-1.5 h-4 bg-purple-500 rounded-full"></div>
                                            发现模版
                                            <span class="text-xs font-normal text-muted-foreground/70 ml-1">({{
                                                filteredDiscoverAgents.length }})</span>
                                        </h3>
                                        <div
                                            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 animate-fade-in">
                                            <AgentCard v-for="agent in filteredDiscoverAgents" :key="agent.id"
                                                :agent="agent" 
                                                :selected="currentAgent?.id === agent.id"
                                                @click="handleAgentClick" @edit="editAgent"
                                                @delete="deleteAgent" />
                                        </div>
                                    </div>
                                </div>
                            </template>

                            <!-- Standard View for other tabs -->
                            <div v-else>
                                <!-- Discover Tab Banner -->
                                <div v-if="activeTab === 'discover' && discoverAgents.length > 0"
                                    class="relative w-full h-48 rounded-xl overflow-hidden mb-8 group">
                                    <!-- Background with animated gradient -->
                                    <div class="absolute inset-0 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 animate-gradient-xy"></div>
                                    
                                    <!-- Dynamic overlay blobs -->
                                    <div class="absolute inset-0 overflow-hidden">
                                        <div class="absolute -top-1/2 -left-1/2 w-full h-full bg-purple-500/20 rounded-full blur-[100px] animate-blob"></div>
                                        <div class="absolute top-0 right-0 w-3/4 h-3/4 bg-blue-500/20 rounded-full blur-[100px] animate-blob animation-delay-2000"></div>
                                        <div class="absolute -bottom-1/2 left-1/4 w-3/4 h-3/4 bg-cyan-500/20 rounded-full blur-[100px] animate-blob animation-delay-4000"></div>
                                    </div>



                                    <!-- Content -->
                                    <div class="relative h-full flex flex-col justify-center px-10 z-10">
                                        <!-- Tech Tag -->
                                        <div class="flex items-center gap-2 mb-4">
                                            <div
                                                class="px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-400/20 backdrop-blur-sm flex items-center gap-2 shadow-[0_0_10px_rgba(59,130,246,0.1)]">
                                                <span class="relative flex h-2 w-2">
                                                    <span
                                                        class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                                    <span
                                                        class="relative inline-flex rounded-full h-2 w-2 bg-blue-500 shadow-[0_0_5px_#3b82f6]"></span>
                                                </span>
                                            </div>
                                        </div>

                                        <!-- Main Title with Glowing Gradient -->
                                        <h1 class="text-4xl font-extrabold tracking-tight mb-3">
                                            <span data-splitting
                                                class="splitting-bounce inline-block text-cyan-300 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                                                预置智能体模版
                                            </span>
                                            <br />
                                            <span data-splitting
                                                class="splitting-bounce inline-block text-white drop-shadow-md">
                                                开箱即用！
                                            </span>
                                        </h1>

                                        <!-- Subtitle with better typography -->
                                        <p
                                            class="text-slate-300/80 text-sm max-w-lg leading-relaxed border-l-2 border-blue-500/30 pl-4 mt-2">
                                            汇聚行业最佳实践与专家经验，一键复用高质量智能体模版，<br>
                                            快速构建您的专属 <span class="text-blue-300 font-medium glow-text">AI 生产力工具</span>。
                                        </p>
                                    </div>

                                    <!-- Decorative Elements with Infinite Scroll -->
                                    <div class="absolute right-0 top-0 bottom-0 w-2/5 z-0 overflow-hidden pointer-events-none mask-image-linear-gradient">
                                        <!-- Scrolling Container -->
                                        <div ref="cardsContainer" class="flex flex-col gap-3 p-4 opacity-90 w-full pl-10 pr-6">
                                            <div 
                                                v-for="(agent, idx) in infiniteAgents" 
                                                :key="idx" 
                                                class="p-3 border border-white/10 rounded-lg flex items-center gap-3 w-full"
                                            >
                                                <component :is="agent.iconComponent" class="w-4 h-4 text-blue-200 shrink-0" />
                                                <div class="min-w-0 flex-1">
                                                    <div class="text-xs font-semibold text-white truncate tracking-wide">{{ agent.name }}</div>
                                                    <div class="text-[10px] text-slate-400 truncate opacity-80">{{ agent.description }}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Filter Bar -->
                                <div class="flex items-center gap-2 mb-6 overflow-x-auto pb-2 custom-scrollbar">
                                    <Button 
                                        v-for="cat in discoverCategories" 
                                        :key="cat"
                                        @click="selectedCategory = cat"
                                        size="sm"
                                        :variant="selectedCategory === cat ? 'default' : 'outline'"
                                        class="rounded-full h-8 text-xs font-medium transition-all whitespace-nowrap shadow-sm shrink-0"
                                    >
                                        {{ cat }}
                                    </Button>
                                </div>

                                <!-- Grouped List -->
                                <div class="flex flex-col gap-8">
                                    <div v-for="(group, category) in groupedAgents" :key="category" class="animate-fade-in">
                                         <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2 pl-1 mb-4">
                                            <div class="w-1 h-4 rounded-full bg-slate-400"></div>
                                            {{ category }}
                                            <span class="text-xs font-normal text-muted-foreground ml-1">({{ group.length }})</span>
                                        </h3>
                                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                                            <AgentCard v-for="agent in group" :key="agent.id" 
                                                :agent="agent"
                                                :selected="currentAgent?.id === agent.id"
                                                @click="handleAgentClick" @edit="editAgent" @delete="deleteAgent" />
                                        </div>
                                    </div>
                                    
                                    <div v-if="Object.keys(groupedAgents).length === 0" class="text-center py-10 text-muted-foreground text-sm">
                                        暂无符合条件的智能体
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Empty State -->
                        <div v-else
                            class="flex-1 flex flex-col items-center justify-center text-center min-h-[400px]">
                            <div class="w-24 h-24 bg-muted/50 rounded-full flex items-center justify-center mb-6 ring-8 ring-muted/20">
                                <Search v-if="searchQuery" class="w-10 h-10 text-muted-foreground/50" />
                                <Box v-else class="w-10 h-10 text-muted-foreground/50" />
                            </div>
                            <h3 class="text-xl font-semibold tracking-tight text-foreground mb-2">{{ searchQuery ? '未找到相关智能体' : '暂无智能体' }}</h3>
                            <p class="text-muted-foreground text-sm max-w-sm mx-auto mb-8">{{ searchQuery ? '请尝试更换关键词搜索，或创建新的智能体。' : '当前暂无智能体，您可以点击下方按钮创建一个新的智能体助手。' }}</p>
                            <Button v-if="!searchQuery && activeTab !== 'discover'" 
                                @click="openCreateModal"
                                class="px-8 shadow-sm hover:scale-105 transition-transform"
                            >
                                <Plus class="w-4 h-4 mr-2" />
                                立即创建
                            </Button>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <AgentEditorDrawer 
            :visible="showDrawer" 
            :agent="currentAgent"
            :mode="drawerMode"
            :knowledgeBases="knowledgeBases"
            :availableModels="availableModels"
            @close="closeDrawer" 
            @saved="handleAgentSaved" 
        />

        <AlertDialog :open="isDeleteDialogOpen" @update:open="val => isDeleteDialogOpen = val">
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>确定要删除智能体 "{{ agentToDelete?.name }}" 吗？</AlertDialogTitle>
                    <AlertDialogDescription>
                        此操作无法撤销。这将永久删除该智能体及其所有配置。
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>取消</AlertDialogCancel>
                    <AlertDialogAction @click="confirmDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                        {{ isDeleting ? '删除中...' : '删除' }}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, h, createVNode, watch, nextTick, onUnmounted, markRaw, defineComponent } from 'vue';
import Splitting from "splitting";
import "splitting/dist/splitting.css";
import gsap from 'gsap';

import Loading from '@/shared/components/atoms/Loading/Loading.vue';
import { useToast } from '@/components/ui/toast/use-toast';
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
import AgentEditorDrawer from './AgentEditorDrawer.vue';
import AgentCard from './AgentCard.vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
    Search, Plus, Box, X, RefreshCw,
    Globe, BarChart, FileText, BookOpen, Lightbulb, Presentation 
} from 'lucide-vue-next';

const { toast } = useToast();

// Icons
const activeTab = ref('all');
const myAgents = ref([]);
const discoverAgents = ref([]);
const availableModels = ref([]);
const knowledgeBases = ref([]);
const showDrawer = ref(false);
const drawerMode = ref('edit');
const currentAgent = ref(null);
const isLoading = ref(true);
const cardsContainer = ref(null);
let animationCtx = null;

const isDeleteDialogOpen = ref(false);
const agentToDelete = ref(null);
const isDeleting = ref(false);

const infiniteAgents = computed(() => {
    const source = discoverAgents.value;
    if (source.length === 0) return [];
    let result = [...source];
    // Ensure enough items for smooth scroll
    while (result.length < 6) {
        result = [...result, ...source];
    }
    // Triple it for seamless loop (1/3 view, 1/3 buffer, 1/3 scroll)
    return [...result, ...result, ...result];
});

const initCardAnimation = () => {
    if (!cardsContainer.value) return;
    if (animationCtx) animationCtx.revert();
    
    animationCtx = gsap.context(() => {
        // Wait for render
        setTimeout(() => {
             if (!cardsContainer.value || !cardsContainer.value.firstElementChild) return;
             
             const itemHeight = cardsContainer.value.firstElementChild.offsetHeight;
             // Get gap from computed style to be precise
             const gap = parseFloat(getComputedStyle(cardsContainer.value).rowGap) || 12;
             const singleSetCount = infiniteAgents.value.length / 3;
             
             // Distance to scroll = Height of one set + gaps
             const distance = singleSetCount * (itemHeight + gap);
             
             gsap.fromTo(cardsContainer.value, 
                { y: 0 },
                {
                    y: -distance,
                    duration: 40, // Slow speed
                    ease: "none",
                    repeat: -1
                }
             );
        }, 200);
    });
};

onMounted(() => {
    fetchAgents();
    fetchKnowledgeBases();
    fetchModels();
    Splitting();
});

onUnmounted(() => {
    if (animationCtx) animationCtx.revert();
});

const searchQuery = ref('');
const selectedCategory = ref('全部');
const showSuggestions = ref(false);

const availableIcons = {
    'globe': Globe,
    'chart': BarChart,
    'book': BookOpen,
    'document': FileText,
    'presentation': Presentation,
    'lightbulb': Lightbulb
};

const getIconComponent = (iconName) => {
    return availableIcons[iconName] || Globe;
};

const currentTabAgents = computed(() => {
    let source = [];
    if (activeTab.value === 'all') {
        source = [...myAgents.value, ...discoverAgents.value];
    } else if (activeTab.value === 'my-agents') {
        source = myAgents.value;
    } else if (activeTab.value === 'discover') {
        source = discoverAgents.value;
    }
    return source;
});

const filterAgents = (agents, query) => {
    // Server-side filtering is implemented, so we return the agents directly
    return agents;
};

const displayedAgents = computed(() => {
    let agents = [];
    if (activeTab.value === 'all') {
        agents = [...myAgents.value, ...discoverAgents.value];
    } else if (activeTab.value === 'my-agents') {
        agents = myAgents.value;
    } else if (activeTab.value === 'discover') {
        agents = discoverAgents.value;
    }
    
    if (!searchQuery.value) return agents;
    
    const query = searchQuery.value.toLowerCase();
    return agents.filter(agent => 
        agent.name.toLowerCase().includes(query) || 
        (agent.description && agent.description.toLowerCase().includes(query))
    );
});

const filteredMyAgents = computed(() => {
    if (!searchQuery.value) return myAgents.value;
    const query = searchQuery.value.toLowerCase();
    return myAgents.value.filter(agent => 
        agent.name.toLowerCase().includes(query) || 
        (agent.description && agent.description.toLowerCase().includes(query))
    );
});

const filteredDiscoverAgents = computed(() => {
    let agents = discoverAgents.value;
    
    // Category filter
    if (selectedCategory.value !== '全部') {
        agents = agents.filter(a => a.category === selectedCategory.value);
    }
    
    if (!searchQuery.value) return agents;
    
    const query = searchQuery.value.toLowerCase();
    return agents.filter(agent => 
        agent.name.toLowerCase().includes(query) || 
        (agent.description && agent.description.toLowerCase().includes(query))
    );
});

const discoverCategories = computed(() => {
    // Collect categories from both myAgents and discoverAgents so custom categories show up
    const categories = new Set(currentTabAgents.value.map(a => a.category).filter(Boolean));
    return ['全部', ...Array.from(categories)];
});

const groupedAgents = computed(() => {
    const groups = {};
    // Use currentTabAgents and apply category filter and search query
    let agentsToGroup = currentTabAgents.value;
    
    // Category filter
    if (selectedCategory.value !== '全部') {
        agentsToGroup = agentsToGroup.filter(a => a.category === selectedCategory.value);
    }
    
    // Search query filter
    if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        agentsToGroup = agentsToGroup.filter(agent => 
            agent.name.toLowerCase().includes(query) || 
            (agent.description && agent.description.toLowerCase().includes(query))
        );
    }
    
    agentsToGroup.forEach(agent => {
        const cat = agent.category || '未分类';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(agent);
    });
    return groups;
});

const searchSuggestions = ref([]);

const fetchSuggestions = async () => {
    // If suggestions are not shown, no need to fetch (e.g. after selection or blur)
    if (!searchQuery.value || !showSuggestions.value) {
        searchSuggestions.value = [];
        return;
    }
    try {
        let url = `/api/v1/agents/?limit=10&q=${encodeURIComponent(searchQuery.value)}`;
        if (activeTab.value === 'my-agents') {
            url += '&is_template=false';
        } else if (activeTab.value === 'discover') {
            url += '&is_template=true';
        }
        const res = await fetch(url);
        if (res.ok) {
            const agents = await res.json();
            // Dedup names
            const names = new Set(agents.map(a => a.name));
            searchSuggestions.value = Array.from(names).slice(0, 5);
        }
    } catch (e) {
        console.error("Failed to fetch suggestions", e);
    }
};

const debouncedFetchSuggestions = ((fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
})(fetchSuggestions, 300);

const isSelectingSuggestion = ref(false);

const selectSuggestion = (suggestion) => {
    isSelectingSuggestion.value = true;
    searchQuery.value = suggestion;
    showSuggestions.value = false;
    // Reset flag after a short delay to allow watcher to skip
    nextTick(() => {
        isSelectingSuggestion.value = false;
    });
};

const handleSearchFocus = () => {
    showSuggestions.value = true;
    if (searchQuery.value) {
        debouncedFetchSuggestions();
    }
};

const handleSearchInput = () => {
    showSuggestions.value = true;
    isSelectingSuggestion.value = false; // Ensure we are in input mode
};

const handleSearchBlur = () => {
    // Delay to allow click on suggestion
    setTimeout(() => {
        showSuggestions.value = false;
    }, 200);
};

const fetchAgents = async () => {
    isLoading.value = true;
    try {
        let url = '/api/v1/agents/?limit=100';
        
        if (searchQuery.value) {
            url += `&q=${encodeURIComponent(searchQuery.value)}`;
        }

        if (activeTab.value === 'my-agents') {
            url += '&is_template=false';
        } else if (activeTab.value === 'discover') {
            url += '&is_template=true';
        }

        const res = await fetch(url);
        if (res.ok) {
            const agents = await res.json();
            
            // Process agents (categories, icons)
            const processedAgents = agents.map(agent => {
                // Map icon strings to components
                const gradients = [
                    'linear-gradient(140.57deg, #ff9ba2 17.28%, #f56a79 91.19%)',
                    'linear-gradient(180deg, #a7c0ff 0%, #6892fd 100%)',
                    'linear-gradient(180deg, #73f1bb 0%, #49dd9d 100%)',
                    'linear-gradient(180deg, #ffc56e 0%, #ffb153 100%)',
                    'linear-gradient(135.82deg, #d194ff 0%, #8a8eff 93.32%)',
                    'linear-gradient(132.83deg, #46c3ff 14.35%, #47aafd 84.99%)'
                ];
                if (agent.is_template) {
                     agent.gradient = gradients[agent.name.length % gradients.length];
                }
                const iconComp = availableIcons[agent.icon] || Globe;
                agent.iconComponent = markRaw(iconComp);
                
                // Assign categories if missing
                if (!agent.category) {
                     agent.category = agent.is_template ? '未分类' : '我的助手';
                }
                return agent;
            });

            // Using backend filtering result directly
            if (activeTab.value === 'my-agents') {
                 myAgents.value = processedAgents;
                 // Don't clear discoverAgents as it might be cached/needed
                 // discoverAgents.value = []; 
            } else if (activeTab.value === 'discover') {
                 // myAgents.value = [];
                 discoverAgents.value = processedAgents;
            } else {
                 // 'all' tab: we might need to separate them if backend returns mixed list
                 // But backend currently returns all if no filter is applied
                 myAgents.value = processedAgents.filter(a => !a.is_template);
                 discoverAgents.value = processedAgents.filter(a => a.is_template);
            }
        } else {
            throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
        }
    } catch (e) {
        console.error("Failed to fetch agents", e);
        // Error handling: Clear lists on error
         myAgents.value = [];
         discoverAgents.value = [];
         toast({
            description: "获取智能体列表失败",
            variant: "destructive"
         });
    } finally {
        isLoading.value = false;
        if (activeTab.value === 'discover') {
            nextTick(() => {
                initCardAnimation();
                Splitting();
            });
        }
    }
};

const debouncedFetchAgents = ((fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
})(fetchAgents, 300);

watch(searchQuery, () => {
    if (isSelectingSuggestion.value) {
        // Trigger search immediately without debounce if selecting from suggestion
        fetchAgents();
        return;
    }
    // Only fetch if query is empty or long enough to avoid spamming
    debouncedFetchAgents();
    debouncedFetchSuggestions();
});

watch(activeTab, () => {
    fetchAgents();
});

const fetchKnowledgeBases = async () => {
    try {
        const res = await fetch('/api/v1/knowledge/list');
        if (res.ok) {
            knowledgeBases.value = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch knowledge bases", e);
    }
};

const fetchModels = async () => {
    try {
        const res = await fetch('/api/v1/llm/models');
        if (res.ok) {
            const allModels = await res.json();
            availableModels.value = allModels.filter(m => m.is_active);
        }
    } catch (e) {
        console.error("Failed to fetch models", e);
    }
};

const openCreateModal = () => {
    currentAgent.value = null;
    drawerMode.value = 'create';
    showDrawer.value = true;
};

const handleAgentClick = (agent) => {
    if (agent.is_template) {
        currentAgent.value = agent;
        drawerMode.value = 'preview';
        showDrawer.value = true;
    } else {
        editAgent(agent);
    }
};

const editAgent = (agent) => {
    currentAgent.value = agent;
    drawerMode.value = 'edit';
    showDrawer.value = true;
};

const deleteAgent = (agent) => {
    agentToDelete.value = agent;
    isDeleteDialogOpen.value = true;
};

const confirmDelete = async () => {
    if (!agentToDelete.value) return;
    isDeleting.value = true;
    try {
        const res = await fetch(`/api/v1/agents/${agentToDelete.value.id}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            await fetchAgents();
            toast({
                description: "删除成功",
            });
        } else {
             throw new Error("Deletion failed");
        }
    } catch (e) {
        toast({
            description: "删除失败",
            variant: "destructive"
        });
    } finally {
        isDeleting.value = false;
        isDeleteDialogOpen.value = false;
        agentToDelete.value = null;
    }
};

const closeDrawer = () => {
    showDrawer.value = false;
    currentAgent.value = null;
};

const handleAgentSaved = () => {
    fetchAgents();
};
</script>

<style scoped>
@keyframes slide-in-right {
    from {
        transform: translateX(100%);
        opacity: 0;
    }

    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.animate-slide-in-right {
    animation: slide-in-right 0.3s ease-out forwards;
}

/* Splitting.js Animation */
:deep(.splitting-bounce .char) {
    animation: bounce-text 2s ease-in-out infinite;
    animation-delay: calc(0.1s * var(--char-index));
    display: inline-block;
    color: inherit;
}

@keyframes bounce-text {
    0%,
    100% {
        transform: translateY(0);
        text-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
    }

    50% {
        transform: translateY(-10px);
        text-shadow: 0 0 25px rgba(59, 130, 246, 0.8), 0 0 10px rgba(59, 130, 246, 0.4);
    }
}

@keyframes blob {
    0% { transform: translate(0px, 0px) scale(1); }
    33% { transform: translate(30px, -50px) scale(1.1); }
    66% { transform: translate(-20px, 20px) scale(0.9); }
    100% { transform: translate(0px, 0px) scale(1); }
}

.animate-blob {
    animation: blob 7s infinite;
}

.animation-delay-2000 {
    animation-delay: 2s;
}

.animation-delay-4000 {
    animation-delay: 4s;
}

@keyframes gradient-xy {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.animate-gradient-xy {
    background-size: 200% 200%;
    animation: gradient-xy 15s ease infinite;
}
</style>
