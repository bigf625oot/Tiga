<template>
    <div v-show="visible" class="flex flex-col h-full border-l bg-background border-border w-[400px] shadow-xl transition-all duration-300 relative z-10">
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-border shrink-0 bg-card/80 backdrop-blur-sm z-20">
            <div class="flex items-center gap-2.5">
                <div class="flex flex-col gap-0.5">
                    <h3 class="font-semibold text-foreground text-lg leading-none">知识问答</h3>
                </div>
            </div>
            <div class="flex items-center gap-1">
                <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80 transition-colors" @click="toggleHistoryPanel" title="历史会话">
                    <MessageSquare class="w-4 h-4 text-muted-foreground/70" />
                </Button>
                <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80 transition-colors" @click="confirmClearChatHistory" title="新会话">
                    <Plus class="w-4 h-4 text-muted-foreground/70" />
                </Button>
                <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-red-50 hover:text-red-500 transition-colors" @click="$emit('close')" title="关闭">
                    <X class="w-4 h-4 text-muted-foreground/70" />
                </Button>
            </div>
        </div>

        <!-- History Panel Overlay -->
        <div v-if="showHistoryPanel" class="absolute inset-0 z-20 flex flex-col bg-background/95 backdrop-blur-sm animate-in fade-in slide-in-from-bottom-2">
            <div class="flex items-center justify-between p-4 border-b border-border bg-background">
                <h4 class="font-medium text-sm">会话历史</h4>
                <Button variant="ghost" size="icon" class="h-8 w-8" @click="showHistoryPanel = false">
                    <X class="w-4 h-4" />
                </Button>
            </div>
            <ScrollArea class="flex-1 p-4">
                <div v-if="sessionsLoading" class="flex justify-center py-4">
                    <Loader2 class="w-6 h-6 animate-spin text-muted-foreground" />
                </div>
                <div v-else-if="sessions.length === 0" class="py-8 text-center text-muted-foreground text-xs">
                    暂无历史会话
                </div>
                <div v-else class="space-y-2">
                    <div 
                        v-for="session in sessions" 
                        :key="session.session_id"
                        class="flex items-center justify-between p-3 text-sm transition-colors border rounded-lg cursor-pointer hover:bg-muted/50 border-border group relative"
                        :class="{'bg-muted border-primary/20': session.session_id === currentSessionId}"
                        @click="switchSession(session.session_id)"
                    >
                        <div class="flex-1 min-w-0 mr-2">
                            <div class="font-medium truncate text-foreground mb-1 text-xs">
                                {{ session.preview || '新会话' }}
                            </div>
                            <div class="flex items-center justify-between text-[10px] text-muted-foreground">
                                <span>{{ formatDate(session.last_active) }}</span>
                                <span>{{ session.message_count }} 条对话</span>
                            </div>
                        </div>
                        <Button 
                            variant="ghost" 
                            size="icon"
                            class="h-6 w-6 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive absolute right-2 top-2"
                            @click.stop="deleteSession(session.session_id)"
                        >
                            <Trash2 class="w-3.5 h-3.5" />
                        </Button>
                    </div>
                </div>
            </ScrollArea>
        </div>

        <!-- Messages Area -->
        <div class="flex-1 overflow-hidden relative">
            <ScrollArea class="h-full px-4" ref="chatScrollArea">
                <div class="py-4 space-y-6">
                    <!-- Empty State -->
                    <div v-if="chatMessages.length === 0" class="flex flex-col items-center justify-center min-h-[400px] px-4 py-8 animate-in fade-in zoom-in duration-500">
                        <div class="mb-8 text-center space-y-4">
                            <div class="inline-flex items-center justify-center w-32 h-32 mb-2">
                                <Vue3Lottie
                                    :animationData="animationData"
                                    :height="128"
                                    :width="128"
                                    :loop="true"
                                    :autoPlay="true"
                                />
                            </div>
                            <div class="space-y-2">
                                <h2 class="text-lg font-semibold tracking-tight text-foreground">知识问答助手</h2>
                                <p class="text-sm text-muted-foreground max-w-[280px] mx-auto leading-relaxed">
                                    基于知识图谱与向量检索，为您提供精准的智能问答服务
                                </p>
                            </div>
                        </div>
                        
                        <!-- Mode Cards -->
                        <div class="grid grid-cols-2 gap-3 w-full">
                            <Card 
                                v-for="card in modeCards" 
                                :key="card.id"
                                class="group relative overflow-hidden transition-all duration-300 hover:shadow-md hover:border-primary/50 cursor-pointer bg-card/50 hover:bg-card border-muted"
                            >
                                <CardHeader class="p-3 pb-1 space-y-0">
                                    <div class="flex items-center justify-between mb-2">
                                        <div class="w-8 h-8 rounded-lg bg-background border shadow-sm flex items-center justify-center group-hover:text-primary group-hover:border-primary/30 transition-colors">
                                            <component :is="card.icon" class="w-4 h-4" />
                                        </div>
                                        <ArrowUpRight class="w-3.5 h-3.5 text-muted-foreground/30 group-hover:text-primary/50 transition-colors" />
                                    </div>
                                    <CardTitle class="text-xs font-semibold">{{ card.title }}</CardTitle>
                                </CardHeader>
                                <CardContent class="p-3 pt-1">
                                    <CardDescription class="text-[10px] text-muted-foreground/80 line-clamp-1 mb-2.5">
                                        {{ card.desc }}
                                    </CardDescription>
                                    <div class="space-y-1 pt-1.5 border-t border-border/40">
                                        <div 
                                            v-for="(ex, idx) in card.examples.slice(0, 2)" 
                                            :key="idx"
                                            @click.stop="handleSuggestion(ex)"
                                            class="text-[10px] text-muted-foreground hover:text-primary truncate flex items-center gap-1.5 py-0.5 transition-colors group/item cursor-pointer"
                                            title="点击使用此示例"
                                        >
                                            <div class="w-1 h-1 rounded-full bg-primary/30 group-hover/item:bg-primary transition-colors"></div>
                                            {{ ex }}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>

                    <!-- Messages -->
                    <div v-for="(msg, index) in chatMessages" :key="index" class="flex flex-col gap-2 group animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <!-- User Message -->
                        <div v-if="msg.role === 'user'" class="flex justify-end">
                            <div class="px-4 py-2.5 bg-primary text-primary-foreground rounded-2xl rounded-tr-sm text-sm shadow-sm max-w-[90%] leading-relaxed">
                                {{ msg.content }}
                            </div>
                        </div>
                        
                        <!-- Assistant Message -->
                        <div v-else class="flex gap-3">
                            <Avatar class="h-8 w-8 mt-0.5 border">
                                <AvatarFallback class="bg-primary/10 text-primary text-xs">AI</AvatarFallback>
                            </Avatar>
                            <div class="flex flex-col gap-2 max-w-[95%] w-full overflow-hidden">
                                
                                <!-- 1. Process Nodes (Collapsible) -->
                                <div v-if="msg.steps && msg.steps.length > 0" class="border border-amber-200/40 dark:border-amber-900/40 rounded-xl overflow-hidden mb-2 bg-amber-50/40 dark:bg-amber-950/20 w-full shadow-sm">
                                    <button 
                                        @click="toggleProcess(msg._id || index)"
                                        class="w-full flex items-center justify-between px-3 py-2.5 hover:bg-amber-100/30 dark:hover:bg-amber-900/30 transition-colors group"
                                    >
                                        <div class="flex items-center gap-2 text-xs font-medium text-amber-700/80 dark:text-amber-500/90">
                                            <Brain class="w-3.5 h-3.5" :class="{'animate-pulse': chatLoading && index === chatMessages.length - 1}" />
                                            <span>思考链 ({{ msg.steps.length }} 步)</span>
                                        </div>
                                        <ChevronRight 
                                            class="w-3.5 h-3.5 text-amber-600/50 dark:text-amber-500/50 transition-transform duration-200 group-hover:text-amber-600 dark:group-hover:text-amber-400"
                                            :class="isProcessExpanded(msg._id || index) ? 'rotate-90' : ''"
                                        />
                                    </button>
                                    <div v-show="isProcessExpanded(msg._id || index)" class="bg-background/40 px-3 py-2 border-t border-amber-200/30 dark:border-amber-900/30">
                                        <div class="space-y-3 relative">
                                            <div class="absolute left-[5px] top-1.5 bottom-1.5 w-px bg-amber-200/50 dark:bg-amber-800/30"></div>
                                            <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="flex gap-3 relative">
                                                <div class="flex flex-col items-center pt-1.5 shrink-0 z-10">
                                                    <div class="w-2.5 h-2.5 rounded-full bg-background border-2 border-amber-400/60 dark:border-amber-600/60 shadow-sm"></div>
                                                </div>
                                                <div class="pb-1 min-w-0 flex-1">
                                                    <div class="text-[11px] text-muted-foreground break-words whitespace-pre-wrap font-mono leading-relaxed">
                                                        {{ step.content }}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 2. Content / Data View -->
                                <div class="flex flex-col w-full">
                                    <!-- View Switcher Toolbar (Only if SQL exists) -->
                                    <div v-if="msg.sql_query" class="flex items-center justify-between mb-2">
                                        <div class="text-xs text-muted-foreground font-medium">查询结果</div>
                                        <div class="flex bg-muted p-0.5 rounded-lg">
                                            <button 
                                                @click="setMsgViewMode(msg._id || index, 'table')"
                                                :class="getMsgViewMode(msg._id || index) === 'table' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'"
                                                class="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all"
                                            >
                                                表格视图
                                            </button>
                                            <button 
                                                @click="setMsgViewMode(msg._id || index, 'sql')"
                                                :class="getMsgViewMode(msg._id || index) === 'sql' ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'"
                                                class="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all"
                                            >
                                                SQL查询
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Loading State -->
                                    <div v-if="!msg.content && !msg.data_content && !msg.error_message && chatLoading && msg === chatMessages[chatMessages.length - 1]" class="p-3 bg-muted/30 rounded-2xl rounded-tl-sm border border-border w-fit">
                                        <div class="flex items-center gap-1">
                                            <div class="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                                            <div class="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                                            <div class="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                                        </div>
                                    </div>

                                    <!-- Main Content Area -->
                                    <div v-else class="bg-card text-card-foreground rounded-2xl rounded-tl-sm border border-border overflow-hidden shadow-sm">
                                        
                                        <!-- SQL View -->
                                        <div v-if="getMsgViewMode(msg._id || index) === 'sql' && msg.sql_query" class="relative group/sql p-3">
                                            <pre class="text-xs bg-muted rounded-lg border border-border overflow-x-auto font-mono p-2"><code>{{ msg.sql_query }}</code></pre>
                                            <Button variant="outline" size="icon" class="h-6 w-6 absolute top-4 right-4 opacity-0 group-hover/sql:opacity-100 transition-opacity" @click="copySql(msg.sql_query)">
                                                <Copy class="w-3 h-3" />
                                            </Button>
                                        </div>

                                        <!-- Table / Text View -->
                                        <div 
                                            v-show="getMsgViewMode(msg._id || index) === 'table'"
                                            class="p-4 text-sm leading-relaxed markdown-content"
                                            :class="{ 'no-sources': !msg.sources || msg.sources.length === 0 }"
                                            v-html="renderMarkdown(msg.content, msg.sources && msg.sources.length > 0)"
                                            @click="handleCitationClick($event, msg)"
                                        ></div>

                                        <!-- Chart View -->
                                        <div v-if="msg.chart_config" class="border-t border-border p-3 bg-background/50">
                                            <div class="flex items-center gap-2 mb-2">
                                                <BarChart3 class="w-3.5 h-3.5 text-primary" />
                                                <span class="text-xs font-bold text-foreground">可视化图表</span>
                                            </div>
                                            <div class="h-64 w-full bg-card rounded-lg border border-border">
                                                <ChartFrame :option="processChartOption(msg.chart_config)" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Sources -->
                                <div v-if="msg.sources && msg.sources.length > 0" class="flex flex-col gap-2 mt-1 pl-1">
                                    <div class="text-[10px] text-muted-foreground font-medium flex justify-between items-center">
                                        <span>参考来源</span>
                                        <Badge variant="secondary" class="text-[9px] h-4 px-1.5 font-normal">
                                            {{ scope === 'global' ? '文档视图' : '详情视图' }}
                                        </Badge>
                                    </div>
                                    
                                    <!-- Case 1: Global Scope - Show Document Cards -->
                                    <div v-if="scope === 'global'" class="flex flex-col gap-2">
                                        <div 
                                            v-for="(doc, idx) in getUniqueDocs(msg.sources)" 
                                            :key="idx"
                                            class="flex items-center gap-3 p-2 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors cursor-pointer group"
                                            :title="doc.filename"
                                        >
                                            <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors">
                                                <FileText class="w-4 h-4" />
                                            </div>
                                            <div class="flex flex-col overflow-hidden">
                                                <span class="text-xs font-medium text-foreground truncate">{{ doc.filename || '未知文档' }}</span>
                                                <span class="text-[10px] text-muted-foreground">相关度: {{ Math.round(doc.score * 100) }}%</span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Case 2: Doc Scope - Show Entities and Chunks -->
                                    <div v-else class="flex flex-col gap-3">
                                        <!-- Entities -->
                                        <div v-if="getEntities(msg.sources).length > 0" class="flex flex-wrap gap-1.5">
                                            <div 
                                                v-for="(src, idx) in getEntities(msg.sources)" 
                                                :key="idx"
                                                @click="locateCitationInGraph(src)"
                                                class="px-2 py-1 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded text-[10px] text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 hover:border-indigo-200 dark:hover:border-indigo-700 transition-colors cursor-pointer flex items-center gap-1"
                                                :title="src.content"
                                            >
                                                <Share2 class="w-3 h-3" />
                                                <span class="font-medium">{{ src.title }}</span>
                                            </div>
                                        </div>

                                        <!-- Chunks -->
                                        <div class="grid grid-cols-1 gap-2">
                                            <div 
                                                v-for="(src, idx) in getChunks(msg.sources).slice(0, 3)" 
                                                :key="idx"
                                                @click="locateCitationInGraph(src)"
                                                class="p-2 bg-card border border-border rounded text-[11px] text-muted-foreground hover:bg-accent/50 hover:border-primary/30 transition-colors cursor-pointer relative group"
                                            >
                                                <div class="flex items-center gap-2 mb-1">
                                                    <span class="px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border text-[9px] font-mono">
                                                        #{{ idx + 1 }}
                                                    </span>
                                                    <span class="text-[9px] text-muted-foreground truncate flex-1">{{ src.title }}</span>
                                                </div>
                                                <div class="line-clamp-2 leading-relaxed opacity-80 group-hover:opacity-100">
                                                    {{ src.content }}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Loading Indicator for new message -->
                    <div v-if="chatLoading && (chatMessages.length === 0 || chatMessages[chatMessages.length - 1].role !== 'assistant')" class="flex gap-3 animate-in fade-in duration-300">
                         <Avatar class="h-8 w-8 mt-0.5 border ring-2 ring-primary/5">
                            <AvatarFallback class="bg-primary/10 text-primary font-semibold">AI</AvatarFallback>
                        </Avatar>
                        <div class="flex items-center gap-1.5 p-4 bg-muted/40 rounded-2xl rounded-tl-sm w-fit border border-border/50 shadow-sm">
                            <div class="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                            <div class="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
                            <div class="w-2 h-2 bg-primary/80 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
                        </div>
                    </div>
                </div>
            </ScrollArea>
        </div>

        <!-- Input Area -->
        <div class="mt-auto pt-4 pb-6 px-4 border-t border-border bg-background/80 backdrop-blur-sm shadow-[0_-5px_20px_-5px_rgba(0,0,0,0.03)] z-20">
            <div class="relative group">
                <Textarea 
                    v-model="chatInput" 
                    @keydown.enter.prevent="handleInputKeydown"
                    placeholder="输入您的问题..." 
                    class="min-h-[52px] max-h-[200px] pr-12 py-3.5 rounded-xl resize-none border-muted-foreground/20 shadow-sm transition-all duration-300 focus:ring-2 focus:ring-primary/20 focus:border-primary/50 bg-background/50 hover:bg-background hover:border-primary/30 scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent"
                    :disabled="chatLoading"
                />
                <Button 
                    size="icon"
                    class="absolute right-2 bottom-2 h-9 w-9 rounded-lg bg-gradient-to-br from-primary to-primary/90 hover:to-primary shadow-md hover:shadow-lg hover:scale-105 transition-all duration-300"
                    :disabled="chatLoading || !chatInput.trim()"
                    @click="sendChatMessage"
                >
                    <ArrowUpRight class="w-5 h-5 text-primary-foreground" />
                </Button>
            </div>
            <div class="flex items-center justify-center gap-1.5 text-[10px] text-muted-foreground/60 mt-3 font-medium select-none">
                <Sparkles class="w-3 h-3 text-primary/40" />
                由混合检索引擎提供支持 (BM25 + Vector + Graph)
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, nextTick, createVNode, onMounted, h } from 'vue';
import axios from 'axios';
import { message, Modal } from 'ant-design-vue';
import { marked } from 'marked';
import ChartFrame from '@/features/analytics/components/ChartFrame.vue';
import { useChartOptimizer } from '@/features/analytics/composables/useChartOptimizer';
import * as echarts from 'echarts';
import { Vue3Lottie } from 'vue3-lottie';
import animationData from '@/assets/data.json';

// Shadcn UI Components
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { 
    Bot, 
    History, 
    Plus, 
    X, 
    Trash2, 
    Sparkles, 
    ChevronRight, 
    Copy, 
    BarChart3, 
    FileText, 
    Share2, 
    Send,
    Loader2,
    ArrowUpRight,
    AlertCircle,
    Info,
    Brain,
    MessageSquare,
    Search,
    Wand2,
    Cpu,
    Zap,
    SendHorizontal
} from 'lucide-vue-next';

// Props
const props = defineProps<{
    visible: boolean;
    docId?: number | string | null;
    scope: string;
    nodes: any;
}>();

// Emits
const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'locate-node', nodeId: string): void;
}>();

const api = axios.create({ baseURL: '/api/v1' });

// Setup Markdown Renderer
const renderer = new marked.Renderer();
renderer.code = ({ text, lang }) => {
    const code = text;
    const language = lang;
    if (language === 'echarts') {
        const id = 'chart-' + Math.random().toString(36).substr(2, 9);
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) {
                try {
                    let jsonStr = code.trim();
                    if (jsonStr.startsWith('{')) {
                        const option = JSON.parse(jsonStr);
                        const chart = echarts.init(el);
                        chart.setOption(option);
                        new ResizeObserver(() => {
                            chart.resize();
                        }).observe(el);
                    }
                } catch (e) {
                    console.error('ECharts render error:', e);
                    el.innerHTML = `<div class="p-2 text-xs text-red-400 bg-red-50 rounded">图表数据解析失败</div>`;
                }
            }
        }, 50);
        return `<div id="${id}" style="width: 100%; height: 240px; margin: 0.5rem 0;"></div>`;
    }
    return `<pre><code class="language-${language}">${code}</code></pre>`;
};
renderer.text = ({ text }) => text;
marked.use({ renderer: renderer, breaks: true, gfm: true });

interface ChatMessage {
    _id?: string;
    role: string;
    content: string;
    steps?: { content: string; step: number }[];
    sources?: any[];
    sql_query?: string;
    data_content?: string;
    chart_config?: any;
    error_message?: string;
}

// State
const chatMessages = ref<ChatMessage[]>([]);
const chatInput = ref('');
const chatLoading = ref(false);
const chatScrollArea = ref<any>(null); // Ref to ScrollArea component
const currentSessionId = ref<string | null>(null);
const showHistoryPanel = ref(false);
const sessions = ref<any[]>([]);
const sessionsLoading = ref(false);

const expandedProcess = ref(new Set());
const msgViewModes = reactive<Record<string, string>>({});

// Methods
const generateUUID = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

const isProcessExpanded = (id: any) => expandedProcess.value.has(id);
const toggleProcess = (id: any) => {
    if (expandedProcess.value.has(id)) {
        expandedProcess.value.delete(id);
    } else {
        expandedProcess.value.add(id);
    }
};

const getMsgViewMode = (id: any) => msgViewModes[id] || 'table';
const setMsgViewMode = (id: any, mode: string) => {
    msgViewModes[id] = mode;
};

const copySql = (sql: string) => {
    if (!sql) return;
    navigator.clipboard.writeText(sql).then(() => {
        message.success('SQL 已复制');
    });
};

const { optimizeOption } = useChartOptimizer();
const processChartOption = (rawOption: any) => optimizeOption(rawOption);

const modeCards = [
    {
        id: 'auto',
        title: '智能问答',
        icon: Wand2,
        desc: '自动识别意图，智能路由引擎',
        examples: ['分析这份文档的核心观点', '梳理关键实体关系']
    },
    {
        id: 'rag',
        title: '知识检索',
        icon: Search,
        desc: '基于文档内容的精确问答',
        examples: ['什么是切片技术？', '文档中提到了哪些标准？']
    },
    {
        id: 'kg',
        title: '图谱分析',
        icon: Zap,
        desc: '可视化实体关系与结构',
        examples: ['展示5G网络的关系图', '查看核心节点的关联']
    },
    {
        id: 'data',
        title: '数据洞察',
        icon: BarChart3,
        desc: '统计数据查询与报表生成',
        examples: ['统计各省份基站数量', '查询本月订单总额']
    }
];

const toggleHistoryPanel = () => {
    showHistoryPanel.value = !showHistoryPanel.value;
    if (showHistoryPanel.value) {
        fetchSessions();
    }
};

const fetchSessions = async () => {
    const targetDocId = props.docId || 0;
    sessionsLoading.value = true;
    try {
        const res = await api.get(`/knowledge/${targetDocId}/qa/sessions`);
        sessions.value = res.data;
    } catch (e) {
        message.error("获取会话列表失败");
    } finally {
        sessionsLoading.value = false;
    }
};

const switchSession = async (sid: string) => {
    currentSessionId.value = sid;
    showHistoryPanel.value = false;
    await fetchChatHistory(props.docId || 0);
};

const deleteSession = async (sid: string) => {
    Modal.confirm({
        title: '删除会话',
        content: '确定要删除该会话及其所有记录吗？',
        onOk: async () => {
            try {
                await api.delete(`/knowledge/chat/sessions/${sid}`);
                message.success('已删除');
                if (currentSessionId.value === sid) {
                    currentSessionId.value = null;
                    chatMessages.value = [];
                }
                fetchSessions();
            } catch (e) {
                message.error('删除失败');
            }
        }
    });
};

const formatDate = (ts: number) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric' });
};

const scrollToBottom = () => {
    // Try to access the viewport element of the ScrollArea or just the last element
    nextTick(() => {
        // Simple fallback: find the last message and scroll it into view
        const messages = document.querySelectorAll('.animate-in');
        if (messages.length > 0) {
            messages[messages.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    });
};

const fetchChatHistory = async (docId: number | string) => {
    if (docId === null || docId === undefined) return;
    if (!currentSessionId.value) {
        chatMessages.value = [];
        return;
    }

    try {
        const params: any = {};
        if (currentSessionId.value) {
            params.session_id = currentSessionId.value;
        }
        const res = await api.get(`/knowledge/${docId}/qa/history`, { params });
        chatMessages.value = res.data;
        scrollToBottom();
    } catch (e) {
        console.error('Failed to fetch chat history:', e);
    }
};

const handleSuggestion = (text: string) => {
    if (chatLoading.value) return;
    chatInput.value = text;
};

const handleInputKeydown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
};

const sendChatMessage = async () => {
    if (chatLoading.value) return;
    if (!chatInput.value.trim()) return;
    
    const query = chatInput.value;
    
    if (!currentSessionId.value) {
        currentSessionId.value = generateUUID();
    }

    chatMessages.value.push({ role: 'user', content: query });
    chatInput.value = '';
    chatLoading.value = true;
    
    scrollToBottom();
    
    try {
        const history = chatMessages.value.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`);
        
        const payload = { 
            query, 
            history,
            scope: props.docId ? props.scope : 'global',
            mode: 'auto',
            session_id: currentSessionId.value
        };
        
        const url = props.docId 
            ? `/api/v1/knowledge/${props.docId}/qa` 
            : `/api/v1/knowledge/qa`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const assistantMsg = reactive<{
            _id: string;
            role: string;
            content: string;
            sources: any[];
            steps: { content: string; step: number }[];
            sql_query: string;
            data_content: string;
            chart_config: any;
        }>({ 
            _id: `msg_${Date.now()}_assistant`,
            role: 'assistant', 
            content: '', 
            sources: [],
            steps: [], 
            sql_query: '',
            data_content: '',
            chart_config: null
        });
        chatMessages.value.push(assistantMsg);

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        if (reader) {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);
                        if (data.type) {
                            switch (data.type) {
                                case 'text':
                                    assistantMsg.content += data.content;
                                    break;
                                case 'process':
                                    assistantMsg.steps.push({
                                        content: data.content,
                                        step: data.step || assistantMsg.steps.length + 1
                                    });
                                    if (assistantMsg.steps.length === 1) {
                                        expandedProcess.value.add(assistantMsg._id);
                                    }
                                    break;
                                case 'sql':
                                    assistantMsg.sql_query = data.content;
                                    setMsgViewMode(assistantMsg._id, 'sql');
                                    break;
                                case 'data':
                                    assistantMsg.data_content = data.content;
                                    assistantMsg.content += '\n' + data.content;
                                    setMsgViewMode(assistantMsg._id, 'table');
                                    break;
                                case 'chart':
                                    assistantMsg.chart_config = data.content;
                                    break;
                                case 'sources':
                                    assistantMsg.sources = data.content;
                                    break;
                                case 'error':
                                    assistantMsg.content += `\n[Error: ${data.content}]`;
                                    break;
                            }
                        } else {
                            assistantMsg.content += JSON.stringify(data);
                        }
                    } catch (e) {
                        assistantMsg.content += line + '\n';
                    }
                }
                scrollToBottom();
            }
        }
        
        if (buffer.trim()) {
             try {
                 const data = JSON.parse(buffer);
                 if (data.type === 'text') assistantMsg.content += data.content;
             } catch (e) {
                 assistantMsg.content += buffer;
             }
        }
        
        if (chatMessages.value.length <= 2 && showHistoryPanel.value) {
            fetchSessions();
        }
        
    } catch (e: any) {
        console.error(e);
        if (chatMessages.value.length === 0 || chatMessages.value[chatMessages.value.length - 1].role === 'user') {
             chatMessages.value.push({ 
                role: 'assistant', 
                content: `[Error: ${e.message}]`,
                sources: []
            });
        } else {
             const lastMsg = chatMessages.value[chatMessages.value.length - 1];
             lastMsg.content += `\n[Error: ${e.message}]`;
        }
    } finally {
        chatLoading.value = false;
        scrollToBottom();
    }
};

const confirmClearChatHistory = () => {
    Modal.confirm({
        title: '开启新会话？',
        icon: h(AlertCircle, { class: 'text-amber-500 w-5 h-5' }),
        content: '这将开启一个新的空白会话，旧的记录将保留在历史中。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                currentSessionId.value = generateUUID();
                chatMessages.value = [];
                message.success('新会话已开启');
                fetchSessions(); 
            } catch (e: any) {
                message.error('操作失败：' + (e.message));
            }
        }
    });
};

const renderMarkdown = (content: string, hasStructuredSources = false) => {
    if (!content) return '';
    try {
        let inputText = (content || '').trim();
        let thinkHtml = '';
        const thinkStart = inputText.indexOf('<think>');
        if (thinkStart !== -1) {
            const thinkEnd = inputText.indexOf('</think>');
            let thinkContent = '';
            let isPartial = false;
            
            if (thinkEnd !== -1) {
                thinkContent = inputText.substring(thinkStart + 7, thinkEnd);
                inputText = inputText.substring(0, thinkStart) + inputText.substring(thinkEnd + 8);
            } else {
                thinkContent = inputText.substring(thinkStart + 7);
                inputText = inputText.substring(0, thinkStart); 
                isPartial = true;
            }

            if (thinkContent || isPartial) {
                let parsedThink = marked.parse(thinkContent || '正在检索思考中...');
                const parsedThinkStr = typeof parsedThink === 'string' ? parsedThink : '';
                const sanitizedThink = (parsedThinkStr || '').replace(/\[object\s+Object\]/gi, '').trim();
                thinkHtml = `
                <details class="mb-4 rounded-xl border border-amber-200/50 dark:border-amber-900/50 bg-gradient-to-r from-amber-50/50 to-orange-50/30 dark:from-amber-950/20 dark:to-orange-950/10 overflow-hidden group shadow-sm" ${isPartial ? 'open' : ''}>
                    <summary class="px-4 py-2 text-xs font-medium text-amber-700/80 dark:text-amber-400/90 cursor-pointer hover:bg-amber-100/30 dark:hover:bg-amber-900/30 flex items-center gap-2.5 select-none transition-all duration-300">
                        <div class="relative flex items-center justify-center w-4 h-4">
                             <svg class="w-4 h-4 animate-pulse" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.907-3.25"/><path d="M18 18a4 4 0 0 0 1.907-3.25"/></svg>
                        </div>
                        <span class="tracking-wide">深度思考中...</span>
                        <svg class="w-3.5 h-3.5 ml-auto opacity-50 group-open:rotate-180 transition-transform duration-300" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                    </summary>
                    <div class="px-4 py-3 text-xs text-muted-foreground/90 border-t border-amber-200/30 dark:border-amber-900/30 bg-background/40 leading-relaxed animate-in slide-in-from-top-1 duration-300">
                        ${sanitizedThink || '正在构建思维链...'}
                    </div>
                </details>`;
            }
        }

        inputText = inputText.replace(/^(\s*)\*\*([^*]+)\*\*([:：])/gm, '$1**$2** $3');
        inputText = inputText.replace(/\[\[Entity:\s*(.*?)\]\]/g, '<span class="entity-citation" data-entity="$1" title="点击在图谱中定位">$1</span>');
        inputText = inputText.replace(/doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?/gi, '');
        
        if (hasStructuredSources) {
            const refHeaderPattern = /\n+\s*(?:#+\s*)?(?:\*\*)?(References|Sources|参考来源|知识来源|引用|引用文献|Reference Document List)(:|\：)?(?:\*\*)?\s*(\n+|$)/gi;
            inputText = inputText.split(refHeaderPattern)[0];
        }
        
        const echartsRegex = /:::\s*echarts\s*([\s\S]*?):::/g;
        inputText = inputText.replace(echartsRegex, (match, jsonContent) => {
            return `\n\`\`\`echarts\n${jsonContent.trim()}\n\`\`\`\n`;
        });
        
        if (inputText.includes('__SOURCES__')) {
            inputText = inputText.split('__SOURCES__')[0];
        }
        
        inputText = inputText.replace(/^data: /gm, '');
        inputText = inputText.replace(/^event: .*$/gm, '');

        inputText = inputText.replace(/\[+[\s\t]*(?:Source:[\s\t]*)?(\d+)[\s\t]*\]+/gi, '[$1]');
        inputText = inputText.replace(/\n{3,}/g, '\n\n').trim();
        if (hasStructuredSources) {
            inputText = inputText.replace(/\[(\d+)\]/g, (match, num) => {
                return `<span class="citation-icon" data-idx="${parseInt(num)-1}" title="点击在图谱中定位">${match}</span>`;
            });
        } else {
            inputText = inputText.replace(/\[(\d+)\]/g, (match) => {
                return `<span class="citation-index-disabled" title="暂无引用来源">${match}</span>`;
            });
        }
        
        const answerHtml = marked.parse(inputText);
        return thinkHtml + answerHtml;
    } catch (e) {
        console.error('Markdown parse error:', e);
        return content;
    }
};

const handleCitationClick = (e: MouseEvent, msg: any) => {
    const citationTarget = (e.target as HTMLElement).closest('.citation-icon');
    if (citationTarget) {
        e.stopPropagation();
        const idx = parseInt(citationTarget.getAttribute('data-idx') || '-1');
        
        if (idx < 0) return;

        if (!msg.sources || msg.sources.length === 0) {
            Modal.warning({ title: '引用数据缺失', content: '当前回答暂无引用来源。', okText: '关闭' });
            return;
        }

        if (!msg.sources[idx]) return;

        const source = msg.sources[idx];
        if (source.source === 'graph') {
             locateCitationInGraph(source);
        } else if (source.source === 'vector') {
             Modal.info({
                title: `参考来源 [${idx + 1}]`,
                icon: h(Info, { class: 'text-primary w-5 h-5' }),
                width: 600,
                content: createVNode('div', { class: 'space-y-3' }, [
                    createVNode('div', { class: 'text-xs text-muted-foreground flex items-center gap-2 pb-2 border-b border-border' }, [
                        createVNode('span', { class: 'bg-primary/10 text-primary px-1.5 py-0.5 rounded border border-primary/20' }, '文档片段'),
                        createVNode('span', { class: 'font-medium truncate max-w-[300px]' }, source.title || source.filename),
                        createVNode('span', { class: 'ml-auto' }, `相关度: ${Math.round(source.score * 100)}%`)
                    ]),
                    createVNode('div', { class: 'p-3 bg-muted/50 rounded-lg text-sm text-foreground leading-relaxed max-h-[400px] overflow-y-auto font-mono whitespace-pre-wrap' }, source.content)
                ]),
                maskClosable: true,
                okText: '关闭'
             });
        } else {
             Modal.info({
                title: `参考来源 [${idx + 1}]`,
                content: JSON.stringify(source, null, 2),
                maskClosable: true,
                okText: '关闭'
             });
        }
        return;
    }

    const entityTarget = (e.target as HTMLElement).closest('.entity-citation');
    if (entityTarget) {
        e.stopPropagation();
        const entityName = entityTarget.getAttribute('data-entity');
        if (entityName) {
            locateCitationInGraph({ title: entityName, source: 'graph' });
        }
    }
};

const locateCitationInGraph = (source: any) => {
    if (!source) return;
    
    if (!props.nodes || Object.keys(props.nodes).length === 0) {
        message.info('当前无可见图谱数据');
        return;
    }

    if (source.source === 'graph') {
        const entityName = source.title; 
        const matchingNodeId = Object.keys(props.nodes).find(id => {
            const node = props.nodes[id];
            return (node.name === entityName) || (id === entityName);
        });
        if (matchingNodeId) {
            emit('locate-node', matchingNodeId);
            return;
        }
    }
    
    const content = source.content || '';
    const matchingNodeIds = Object.keys(props.nodes).filter(id => {
        const node = props.nodes[id];
        const name = node.name || id;
        return content.includes(name);
    });
    if (matchingNodeIds.length > 0) {
        emit('locate-node', matchingNodeIds[0]);
    } else {
        message.info('未在当前可见图谱中找到相关实体');
    }
};

const getUniqueDocs = (sources: any[]) => {
    if (!sources) return [];
    const docs = new Map();
    sources.forEach(s => {
        if (s.source === 'vector' && s.filename) {
            if (!docs.has(s.filename)) {
                docs.set(s.filename, {
                    filename: s.filename,
                    doc_id: s.doc_id,
                    score: s.score
                });
            } else {
                const existing = docs.get(s.filename);
                if (s.score > existing.score) {
                    existing.score = s.score;
                }
            }
        }
    });
    return Array.from(docs.values()).sort((a: any, b: any) => b.score - a.score);
};

const getChunks = (sources: any[]) => {
    return (sources || []).filter(s => s.source === 'vector');
};

const getEntities = (sources: any[]) => {
    return (sources || []).filter(s => s.source === 'graph');
};

defineExpose({
    renderMarkdown,
    handleCitationClick,
    locateCitationInGraph,
    sendChatMessage
});

onMounted(() => {
    fetchSessions();
});

watch(() => props.visible, (newVal) => {
    if (newVal) {
        scrollToBottom();
    }
});
</script>

<style scoped>
.markdown-content :deep(p) {
    margin-bottom: 0.75rem;
    line-height: 1.6;
}
.markdown-content :deep(p:last-child) {
    margin-bottom: 0;
}
.markdown-content :deep(ul), .markdown-content :deep(ol) {
    padding-left: 1.5rem;
    margin-bottom: 0.75rem;
}
.markdown-content :deep(li) {
    margin-bottom: 0.4rem;
}
.markdown-content :deep(strong) {
    font-weight: 600;
    color: hsl(var(--foreground));
}
.markdown-content :deep(.entity-citation) {
    color: hsl(var(--primary));
    background-color: hsl(var(--primary) / 0.08);
    padding: 2px 6px;
    margin: 0 2px;
    border-radius: 6px;
    border: 1px solid hsl(var(--primary) / 0.2);
    cursor: pointer;
    font-weight: 500;
    font-size: 0.9em;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 2px;
}
.markdown-content :deep(.entity-citation:hover) {
    background-color: hsl(var(--primary) / 0.15);
    transform: translateY(-1px);
    box-shadow: 0 2px 5px -1px hsl(var(--primary) / 0.2);
}
.markdown-content :deep(.citation-icon) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    background-color: hsl(var(--muted)/0.5);
    color: hsl(var(--primary));
    border: 1px solid hsl(var(--border));
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin: 0 1px 0 3px;
    padding: 0 4px;
    cursor: pointer;
    vertical-align: super;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.markdown-content :deep(.citation-icon:hover) {
    background-color: hsl(var(--primary));
    border-color: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    transform: translateY(-2px) scale(1.1);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.markdown-content.no-sources :deep(.citation-icon) {
    pointer-events: none;
    opacity: 0.5;
    cursor: default;
}
.markdown-content :deep(.citation-index-disabled) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    background-color: hsl(var(--muted));
    color: hsl(var(--muted-foreground));
    border: 1px dashed hsl(var(--border));
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin: 0 2px;
    padding: 0 3px;
    vertical-align: super;
}

/* Table Styles */
.markdown-content :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
    font-size: 13px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid hsl(var(--border));
    display: table;
}
.markdown-content :deep(thead) {
    background-color: hsl(var(--muted));
}
.markdown-content :deep(th), .markdown-content :deep(td) {
    border: 1px solid hsl(var(--border));
    padding: 10px 14px;
    text-align: left;
}
.markdown-content :deep(th) {
    background-color: hsl(var(--muted));
    font-weight: 600;
    color: hsl(var(--muted-foreground));
}
.markdown-content :deep(tr:hover) {
    background-color: hsl(var(--muted) / 0.5);
}
.markdown-content :deep(pre) {
    background: hsl(var(--muted));
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid hsl(var(--border));
}
.markdown-content :deep(code) {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
}
</style>
