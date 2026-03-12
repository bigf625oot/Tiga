<template>
    <div class="h-full flex flex-col bg-background overflow-hidden">
        <!-- Compact Header (Knowledge Base Style) -->
        <div
            class="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
            <div class="flex items-center gap-3">
                <h2 class="text-lg font-semibold tracking-tight text-foreground">智能体中心</h2>
                <div class="h-4 w-px bg-border"></div>
                <p class="text-muted-foreground text-xs truncate max-w-xl">
                    管理智能体与应用模版
                </p>
            </div>

            <div class="flex items-center gap-2">
                <Button @click="openCreateModal" size="sm" class="h-9 shadow-sm">
                    <Plus class="mr-2 h-4 w-4" />
                    创建智能体
                </Button>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
            <div class="max-w-[1600px] mx-auto w-full flex flex-col gap-6">

                <Loading v-if="isLoading" type="skeleton-card" />

                <template v-else>
                    <!-- Filter Tabs & Search -->
                    <div class="flex items-center justify-between">
                        <Tabs :model-value="activeTab" @update:model-value="(val) => activeTab = val" class="w-auto">
                            <TabsList class="grid w-full grid-cols-3 h-9 bg-muted/50 p-1">
                                <TabsTrigger value="all" class="text-xs px-4">全部</TabsTrigger>
                                <TabsTrigger value="my-agents" class="text-xs px-4">自定义智能体</TabsTrigger>
                                <TabsTrigger value="discover" class="text-xs px-4">发现模版</TabsTrigger>
                            </TabsList>
                        </Tabs>

                        <div class="relative w-64">
                            <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input v-model="searchQuery" @focus="showSuggestions = true" @blur="handleSearchBlur"
                                @input="showSuggestions = true" placeholder="搜索智能体..."
                                class="pl-8 h-9 bg-muted/50 border-input focus-visible:ring-1 pr-8" />
                            <button v-if="searchQuery" @click="searchQuery = ''; showSuggestions = false"
                                class="absolute right-2 top-2.5 text-muted-foreground hover:text-foreground transition-colors">
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
                    </div>

                    <!-- Agent List -->
                    <div class="flex flex-col gap-6">
                        <!-- Search Header -->
                        <div v-if="searchQuery" class="flex items-center gap-2">
                            <h3 class="text-lg font-semibold tracking-tight text-foreground">搜索结果</h3>
                            <span class="text-sm text-muted-foreground">({{ displayedAgents.length }})</span>
                        </div>

                        <div v-if="displayedAgents.length > 0">
                            <!-- Grouped View for 'all' tab -->
                            <template v-if="activeTab === 'all'">
                                <div class="flex flex-col gap-8">
                                    <div v-if="filteredMyAgents.length > 0" class="flex flex-col gap-4">
                                        <h3
                                            class="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2 pl-1">
                                            <div class="w-1 h-4 bg-blue-500 rounded-full"></div>
                                            自定义智能体
                                            <span class="text-xs font-normal text-muted-foreground ml-1">({{
                                                filteredMyAgents.length }})</span>
                                        </h3>
                                        <div
                                            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 animate-fade-in">
                                            <AgentCard v-for="agent in filteredMyAgents" :key="agent.id" :agent="agent"
                                                @click="handleAgentClick" @edit="editAgent" @delete="deleteAgent" />
                                        </div>
                                    </div>

                                    <div v-if="filteredDiscoverAgents.length > 0" class="flex flex-col gap-4">
                                        <h3
                                            class="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2 pl-1">
                                            <div class="w-1 h-4 bg-purple-500 rounded-full"></div>
                                            发现模版
                                            <span class="text-xs font-normal text-muted-foreground ml-1">({{
                                                filteredDiscoverAgents.length }})</span>
                                        </h3>
                                        <div
                                            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 animate-fade-in">
                                            <AgentCard v-for="agent in filteredDiscoverAgents" :key="agent.id"
                                                :agent="agent" @click="handleAgentClick" @edit="editAgent"
                                                @delete="deleteAgent" />
                                        </div>
                                    </div>
                                </div>
                            </template>

                            <!-- Standard View for other tabs -->
                            <div v-else>
                                <!-- Discover Tab Banner -->
                                <div v-if="activeTab === 'discover'"
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
                                                <div class="p-2 rounded-md bg-white/10 shrink-0 flex items-center justify-center shadow-inner">
                                                    <component :is="agent.iconComponent" class="w-4 h-4 text-blue-200" />
                                                </div>
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
                                    <button 
                                        v-for="cat in discoverCategories" 
                                        :key="cat"
                                        @click="selectedCategory = cat"
                                        class="px-4 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap border"
                                        :class="selectedCategory === cat ? 'bg-slate-900 text-white border-slate-900 shadow-md' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'"
                                    >
                                        {{ cat }}
                                    </button>
                                </div>

                                <!-- Grouped List -->
                                <div class="flex flex-col gap-8">
                                    <div v-for="(group, category) in groupedDiscoverAgents" :key="category" class="animate-fade-in">
                                         <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2 pl-1 mb-4">
                                            <div class="w-1 h-4 rounded-full bg-slate-400"></div>
                                            {{ category }}
                                            <span class="text-xs font-normal text-muted-foreground ml-1">({{ group.length }})</span>
                                        </h3>
                                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                                            <AgentCard v-for="agent in group" :key="agent.id" :agent="agent"
                                                @click="handleAgentClick" @edit="editAgent" @delete="deleteAgent" />
                                        </div>
                                    </div>
                                    
                                    <div v-if="Object.keys(groupedDiscoverAgents).length === 0" class="text-center py-10 text-muted-foreground text-sm">
                                        暂无符合条件的模版
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Empty State -->
                        <div v-else
                            class="py-16 flex flex-col items-center justify-center text-center bg-muted/30 border border-dashed border-border rounded-lg">
                            <div class="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                                <Search v-if="searchQuery" class="w-8 h-8 text-muted-foreground" />
                                <Box v-else class="w-8 h-8 text-muted-foreground" />
                            </div>
                            <h3 class="text-foreground font-medium mb-1">{{ searchQuery ? '未找到相关智能体' : '暂无智能体' }}</h3>
                            <p class="text-muted-foreground text-sm mb-6">{{ searchQuery ? '请尝试更换关键词' : '当前列表为空' }}</p>
                            <Button v-if="!searchQuery && activeTab !== 'discover'" variant="outline"
                                @click="openCreateModal">
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
    </div>
</template>

<script setup>
import { ref, computed, onMounted, h, createVNode, watch, nextTick, onUnmounted, markRaw, defineComponent } from 'vue';
import Splitting from "splitting";
import "splitting/dist/splitting.css";
import gsap from 'gsap';

import Loading from '@/shared/components/atoms/Loading/Loading.vue';
import { Modal, message } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import AgentEditorDrawer from './AgentEditorDrawer.vue';
import AgentCard from './AgentCard.vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, Plus, Box, X } from 'lucide-vue-next';

// Helper to create simple SVG icons without runtime compiler dependency
const createIcon = (d) => markRaw(defineComponent({
    render: () => h('svg', {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '1.5',
        stroke: 'currentColor'
    }, [
        h('path', {
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            d: d
        })
    ])
}));

// Icons
const GlobeAltIcon = createIcon('M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S12 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S12 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418');
const ChartBarIcon = createIcon('M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z');
const DocumentTextIcon = createIcon('M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z');
const BookOpenIcon = createIcon('M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25');
const LightBulbIcon = createIcon('M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 2.625v1.068a1.5 1.5 0 01-1.5 1.5h-1.5a1.5 1.5 0 01-1.5-1.5v-1.068a25.509 25.509 0 013 0zm-6-2.25a9 9 0 1118 0 9 9 0 01-18 0z');
const PresentationChartLineIcon = createIcon('M3.75 3v11.25A2.25 2.25 0 006 14.25h12a2.25 2.25 0 002.25-2.25V3M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 14.25h-2.25m-7.5 0h2.25m-2.25 0v5.25m0 0h2.25m-2.25 0h-2.25');

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
    'globe': GlobeAltIcon,
    'chart': ChartBarIcon,
    'book': BookOpenIcon,
    'document': DocumentTextIcon,
    'presentation': PresentationChartLineIcon,
    'lightbulb': LightBulbIcon
};

const getIconComponent = (iconName) => {
    return availableIcons[iconName] || GlobeAltIcon;
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
    const categories = new Set(discoverAgents.value.map(a => a.category).filter(Boolean));
    return ['全部', ...Array.from(categories)];
});

const groupedDiscoverAgents = computed(() => {
    const groups = {};
    filteredDiscoverAgents.value.forEach(agent => {
        const cat = agent.category || '其他';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(agent);
    });
    return groups;
});

const searchSuggestions = computed(() => {
    if (!searchQuery.value) return [];
    const query = searchQuery.value.toLowerCase();
    const allAgents = [...myAgents.value, ...discoverAgents.value];
    // Use Set to avoid duplicates
    const names = new Set(allAgents
        .filter(agent => agent.name.toLowerCase().includes(query))
        .map(agent => agent.name));
    return Array.from(names).slice(0, 5);
});

const selectSuggestion = (suggestion) => {
    searchQuery.value = suggestion;
    showSuggestions.value = false;
    fetchAgents();
};

const highlightMatch = (text) => {
    if (!searchQuery.value) return text;
    const regex = new RegExp(`(${searchQuery.value})`, 'gi');
    return text.replace(regex, '<span class="text-blue-500 font-bold">$1</span>');
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
                const iconComp = availableIcons[agent.icon] || GlobeAltIcon;
                agent.iconComponent = markRaw(iconComp);
                
                // Assign categories if missing
                if (!agent.category) {
                    if (['通用智能体', '解决方案'].includes(agent.name) || agent.name.includes('通用')) agent.category = '通用助手';
                    else if (['知识库查询', '政策解读', '顶层规划'].includes(agent.name)) agent.category = '企业办公';
                    else if (['市场洞察', '专题研究'].includes(agent.name)) agent.category = '数据分析';
                    else if (['领导讲话'].includes(agent.name)) agent.category = '内容创作';
                    else agent.category = '其他';
                }
                // Default category for My Agents
                if (!agent.category && !agent.is_template) {
                     agent.category = '我的助手';
                }
                return agent;
            });

            if (activeTab.value === 'my-agents') {
                 myAgents.value = processedAgents;
                 discoverAgents.value = [];
            } else if (activeTab.value === 'discover') {
                 myAgents.value = [];
                 discoverAgents.value = processedAgents;
            } else {
                 myAgents.value = processedAgents.filter(a => !a.is_template);
                 discoverAgents.value = processedAgents.filter(a => a.is_template);
            }
        } else {
            throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
        }
    } catch (e) {
        console.error("Failed to fetch agents", e);
        // Fallback on error too
         const mockAgents = [
             { id: 'ab126f', name: '通用智能体', category: '通用助手', description: '基于大语言模型的通用对话助手，支持多轮对话、上下文理解与多语言翻译。', is_active: true, is_template: false, icon: 'globe' },
             { id: '792a8e', name: '知识库查询', category: '企业办公', description: '专注于企业内部知识库检索与问答，支持文档解析与精准溯源。', is_active: true, is_template: false, icon: 'book' },
             { id: '57f7a0', name: '顶层规划', category: '企业办公', description: '协助进行企业战略规划、顶层设计与宏观分析，提供专业的咨询建议。', is_active: true, is_template: true, icon: 'presentation' },
             { id: '226219', name: '市场洞察', category: '数据分析', description: '分析市场趋势、竞争对手动态与行业数据，生成深度洞察报告。', is_active: true, is_template: true, icon: 'chart' },
             { id: '9c851f', name: '专题研究', category: '数据分析', description: '针对特定领域进行深入研究，整合多源信息，产出高质量研究报告。', is_active: true, is_template: true, icon: 'document' },
             { id: 'f13732', name: '政策解读', category: '企业办公', description: '解读最新政策法规，分析其对企业的影响与应对策略。', is_active: true, is_template: true, icon: 'lightbulb' },
             { id: '9297de', name: '领导讲话', category: '内容创作', description: '辅助撰写各类领导讲话稿，风格严谨，逻辑清晰，符合公文规范。', is_active: true, is_template: true, icon: 'globe' },
             { id: 'bc6255', name: '解决方案', category: '通用助手', description: '针对具体业务痛点提供系统性的解决方案与实施建议。', is_active: true, is_template: true, icon: 'globe' }
         ];
         
         const processedMocks = mockAgents.map(agent => {
            const iconComp = availableIcons[agent.icon] || GlobeAltIcon;
            agent.iconComponent = markRaw(iconComp);
            return agent;
         });

         myAgents.value = processedMocks.filter(a => !a.is_template);
         discoverAgents.value = processedMocks.filter(a => a.is_template);
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
    // Only fetch if query is empty or long enough to avoid spamming
    debouncedFetchAgents();
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
    Modal.confirm({
        title: `确定要删除智能体 "${agent.name}" 吗？`,
        icon: createVNode(ExclamationCircleOutlined),
        content: '删除后将无法恢复，请谨慎操作。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                const res = await fetch(`/api/v1/agents/${agent.id}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    fetchAgents();
                    message.success("删除成功");
                }
            } catch (e) {
                message.error("删除失败");
            }
        }
    });
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
