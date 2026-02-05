<template>
    <div class="flex h-full overflow-hidden bg-white">
        <!-- Left: Graph -->
        <div class="flex-1 border-r border-slate-200 relative">
            <div v-if="graphLoading" class="h-full flex flex-col items-center justify-center p-8 gap-4">
                <!-- Skeleton for Graph -->
                <div class="w-full h-full bg-slate-50 graph-skeleton relative overflow-hidden">
                    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
                        <div class="w-16 h-16 rounded-full bg-slate-200 mb-4"></div>
                        <div class="w-32 h-4 bg-slate-200 rounded"></div>
                    </div>
                    <!-- Random Nodes -->
                    <div class="absolute top-1/4 left-1/4 w-12 h-12 rounded-full bg-slate-200"></div>
                    <div class="absolute bottom-1/4 right-1/4 w-10 h-10 rounded-full bg-slate-200"></div>
                    <div class="absolute top-1/3 right-1/3 w-8 h-8 rounded-full bg-slate-200"></div>
                </div>
            </div>
            <div v-else class="h-full">
                <div v-if="graphReason" class="mb-3 px-3 py-2 bg-amber-50 border border-amber-200 text-amber-700 rounded-lg text-xs">
                    {{ graphReason }}
                </div>
                <GraphViewer ref="graphViewerRef" :nodes="graphNodes" :edges="graphEdges" :hiddenTypes="hiddenTypes" :colorMap="colorMap" :reload="reloadGraph" :scope="graphScope" :switchScope="switchGraphScope" :showScopeToggle="!!docId" />
            </div>
        </div>

        <!-- Right: Chat -->
        <div class="w-[400px] flex flex-col pl-4 bg-white relative border-l border-slate-100">
            
            <!-- Header for Chat -->
            <div class="py-3 border-b border-slate-100 flex justify-between items-center bg-white shrink-0 pr-2">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <span class="w-1 h-4 bg-blue-600 rounded-full"></span>
                    知识问答
                </h3>
                <div class="flex items-center gap-2">
                    <button 
                        @click="toggleHistoryPanel"
                        class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="历史会话"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </button>
                    <button 
                        @click="confirmClearChatHistory" 
                        class="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                        title="开启新会话"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    </button>
                </div>
            </div>

            <!-- History Panel (Overlay) -->
            <div v-if="showHistoryPanel" class="absolute inset-0 bg-white z-20 flex flex-col animate-fade-in-up">
                <div class="flex items-center justify-between p-3 border-b border-slate-100 bg-slate-50">
                    <h4 class="text-sm font-medium text-slate-700">会话历史</h4>
                    <button @click="showHistoryPanel = false" class="text-slate-400 hover:text-slate-600">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                <div class="flex-1 overflow-y-auto p-2 space-y-2">
                    <div v-if="sessionsLoading" class="flex justify-center py-4">
                        <div class="w-5 h-5 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin"></div>
                    </div>
                    <div v-else-if="sessions.length === 0" class="text-center text-xs text-slate-400 py-8">
                        暂无历史会话
                    </div>
                    <div 
                        v-for="session in sessions" 
                        :key="session.session_id"
                        class="p-3 rounded-lg border border-slate-100 hover:border-blue-200 hover:bg-blue-50 cursor-pointer transition-all group relative"
                        :class="{'bg-blue-50 border-blue-200': session.session_id === currentSessionId}"
                        @click="switchSession(session.session_id)"
                    >
                        <div class="text-xs font-medium text-slate-700 mb-1 line-clamp-1 pr-6">
                            {{ session.preview || '新会话' }}
                        </div>
                        <div class="flex items-center justify-between text-[10px] text-slate-400">
                            <span>{{ formatDate(session.last_active) }}</span>
                            <span>{{ session.message_count }} 条对话</span>
                        </div>
                        <button 
                            @click.stop="deleteSession(session.session_id)"
                            class="absolute top-2 right-2 p-1 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Messages Area -->
            <div class="flex-1 overflow-y-auto space-y-6 pr-2 mb-4 pt-4 relative" ref="chatContainer">
                <!-- Empty State -->
                <div v-if="chatMessages.length === 0" class="h-full flex flex-col items-center justify-center text-center px-6">
                    <div class="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
                        <svg class="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                    </div>
                    <h3 class="text-base font-medium text-slate-800 mb-2">问答助手</h3>
                    <p class="text-sm text-slate-500 leading-relaxed">
                        我已阅读完全部数据，您可以问我任何知识中心内容的问题，我会结合知识图谱为您解答。
                    </p>
                    <div class="mt-8 grid grid-cols-1 gap-2 w-full">
                        <div 
                            class="px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs rounded-lg cursor-pointer transition-colors border border-slate-100 text-left"
                            :class="{'opacity-50 pointer-events-none cursor-not-allowed': chatLoading}"
                            @click="handleSuggestion('这份文档主要讲了什么？')"
                        >
                            这份文档主要讲了什么？
                        </div>
                        <div 
                            class="px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs rounded-lg cursor-pointer transition-colors border border-slate-100 text-left"
                            :class="{'opacity-50 pointer-events-none cursor-not-allowed': chatLoading}"
                            @click="handleSuggestion('有哪些关键实体和关系？')"
                        >
                            有哪些关键实体和关系？
                        </div>
                    </div>
                </div>

                <!-- Messages -->
                <div v-for="(msg, index) in chatMessages" :key="index" class="flex flex-col gap-2 group animate-fade-in-up">
                    <!-- User Message -->
                    <div v-if="msg.role === 'user'" class="flex justify-end">
                        <div class="px-4 py-2.5 bg-blue-600 text-white rounded-2xl rounded-tr-sm text-sm shadow-sm max-w-[90%] leading-relaxed">
                            {{ msg.content }}
                        </div>
                    </div>
                    
                    <!-- Assistant Message -->
                    <div v-else class="flex gap-3">
                        <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-1">
                            <svg class="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div class="flex flex-col gap-2 max-w-[90%]">
                            <div 
                                class="p-3 bg-slate-50 text-slate-800 rounded-2xl rounded-tl-sm text-sm leading-relaxed border border-slate-100 markdown-content"
                                v-html="renderMarkdown(msg.content, msg.sources && msg.sources.length > 0)"
                                @click="handleCitationClick($event, msg)"
                            >
                            </div>
                            
                            <!-- Sources -->
                            <div v-if="msg.sources && msg.sources.length > 0" class="flex flex-col gap-2 mt-2 pt-2 border-t border-slate-100">
                                <div class="text-[10px] text-slate-400 font-medium pl-1 flex justify-between items-center">
                                    <span>参考来源</span>
                                    <span v-if="graphScope === 'global'" class="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-500">文档视图</span>
                                    <span v-else class="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-500">详情视图</span>
                                </div>
                                
                                <!-- Case 1: Global Scope - Show Document Cards -->
                                <div v-if="graphScope === 'global'" class="flex flex-col gap-2">
                                    <div 
                                        v-for="(doc, idx) in getUniqueDocs(msg.sources)" 
                                        :key="idx"
                                        class="flex items-center gap-3 p-2 bg-white border border-slate-200 rounded-lg hover:border-blue-300 transition-colors cursor-pointer group"
                                        :title="doc.filename"
                                    >
                                        <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 group-hover:bg-blue-100 transition-colors">
                                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                        </div>
                                        <div class="flex flex-col overflow-hidden">
                                            <span class="text-xs font-medium text-slate-700 truncate">{{ doc.filename || '未知文档' }}</span>
                                            <span class="text-[10px] text-slate-400">相关度: {{ Math.round(doc.score * 100) }}%</span>
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
                                            class="px-2 py-1 bg-indigo-50 border border-indigo-100 rounded text-[10px] text-indigo-600 hover:bg-indigo-100 hover:border-indigo-200 transition-colors cursor-pointer flex items-center gap-1"
                                            :title="src.content"
                                        >
                                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                            <span class="font-medium">{{ src.title }}</span>
                                        </div>
                                    </div>

                                    <!-- Chunks -->
                                    <div class="grid grid-cols-1 gap-2">
                                        <div 
                                            v-for="(src, idx) in getChunks(msg.sources).slice(0, 3)" 
                                            :key="idx"
                                            @click="locateCitationInGraph(src)"
                                            class="p-2 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-600 hover:bg-blue-50 hover:border-blue-300 transition-colors cursor-pointer relative group"
                                        >
                                            <div class="flex items-center gap-2 mb-1">
                                                <span class="px-1.5 py-0.5 rounded bg-white text-slate-500 border border-slate-200 text-[9px] font-mono">
                                                    #{{ idx + 1 }}
                                                </span>
                                                <span class="text-[9px] text-slate-400 truncate flex-1">{{ src.title }}</span>
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
                
                <!-- Loading State -->
                <div v-if="chatLoading" class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-1">
                        <svg class="w-4 h-4 text-indigo-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <div class="flex items-center gap-1 p-3 bg-slate-50 rounded-2xl rounded-tl-sm w-fit">
                        <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                        <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                        <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                    </div>
                </div>
            </div>

            <!-- Input Area -->
            <div class="mt-auto pt-4 border-t border-slate-100 bg-white">
                <div class="relative">
                    <input 
                        v-model="chatInput" 
                        @keyup.enter="sendChatMessage"
                        type="text" 
                        placeholder="输入问题..." 
                        class="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all placeholder:text-slate-400"
                        :disabled="chatLoading"
                    >
                    <button 
                        @click="sendChatMessage"
                        class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm group"
                        :disabled="chatLoading || !chatInput.trim()"
                    >
                        <svg class="w-4 h-4 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                    </button>
                </div>
                <div class="text-[10px] text-center text-slate-300 mt-2 pb-1">
                    由混合检索引擎提供支持 (BM25 + Vector + Graph)
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, createVNode, computed } from 'vue';
import axios from 'axios';
import { message, Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { marked } from 'marked';
import GraphViewer from './common/GraphViewer.vue';

const props = defineProps({
    docId: {
        type: [Number, String],
        default: null
    },
    initialScope: {
        type: String,
        default: 'doc'
    }
});

const api = axios.create({ baseURL: '/api/v1' });

// Markdown rendering configuration
const renderer = new marked.Renderer();
renderer.text = ({ text }) => text;
marked.use({
    renderer: renderer,
    breaks: true,
    gfm: true
});

// State
const graphLoading = ref(false);
const graphReason = ref('');
const graphNodes = ref({});
const graphEdges = ref({});
const graphScope = ref(props.initialScope);
const hiddenTypes = ref([]);
const colorMap = ref({});
const colorChips = ref([]);
const graphViewerRef = ref(null);

const chatMessages = ref([]);
const chatInput = ref('');
const chatLoading = ref(false);
const chatContainer = ref(null);
const currentSessionId = ref(null);

// History Panel
const showHistoryPanel = ref(false);
const sessions = ref([]);
const sessionsLoading = ref(false);

const toggleHistoryPanel = () => {
    showHistoryPanel.value = !showHistoryPanel.value;
    if (showHistoryPanel.value) {
        fetchSessions();
    }
};

const fetchSessions = async () => {
    if (!props.docId) return;
    sessionsLoading.value = true;
    try {
        const res = await api.get(`/knowledge/${props.docId}/qa/sessions`);
        sessions.value = res.data;
    } catch (e) {
        message.error("获取会话列表失败");
    } finally {
        sessionsLoading.value = false;
    }
};

const switchSession = async (sid) => {
    currentSessionId.value = sid;
    showHistoryPanel.value = false;
    await fetchChatHistory(props.docId);
};

const deleteSession = async (sid) => {
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

const formatDate = (ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric' });
};

const generateUUID = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

const baseColorMap = {
  "人": "#4F81BD",
  "组织": "#9F4C7C",
  "事件": "#C0504D",
  "文档": "#9BBB59",
  "资产": "#8064A2"
};
const knownTypeOrder = ["人","组织","事件","文档","资产"];

// Lifecycle
onMounted(() => {
    initView();
});

watch(() => props.docId, () => {
    initView();
});

const initView = () => {
    if (!props.docId && props.initialScope !== 'global') {
        // If no docId, force global
        graphScope.value = 'global';
    } else {
        graphScope.value = props.initialScope;
    }
    
    // Reset Chat
    chatMessages.value = [];
    chatInput.value = '';
    showHistoryPanel.value = false;
    
    // Reset session on view init
    currentSessionId.value = null;

    // Do not fetch mixed history by default. Start with empty chat.
    // User can load history from the panel.
    if (props.docId) {
        fetchSessions();
    }
    
    loadGraphData();
};

// Graph Methods
const loadGraphData = async () => {
    graphLoading.value = true;
    graphNodes.value = {};
    graphEdges.value = {};
    graphReason.value = '';
    
    try {
        const url = graphScope.value === 'global' ? `/knowledge/graph` : `/knowledge/${props.docId}/graph`;
        const res = await api.get(url);
        if (res.data) {
            graphNodes.value = res.data.nodes || {};
            graphEdges.value = res.data.edges || {};
            graphReason.value = mapGraphReason(res.data.reason || '');
            assignTypesFromAttributes();
            rebuildFilterFromGraph();
        }
    } catch (e) {
        console.error(e);
        message.error("获取图谱数据失败: " + (e.response?.data?.detail || e.message));
    } finally {
        graphLoading.value = false;
    }
};

const reloadGraph = () => loadGraphData();

const switchGraphScope = (scope) => {
    if (graphScope.value === scope) return;
    graphScope.value = scope;
    loadGraphData();
};

const mapGraphReason = (reason) => {
    if (!reason) return '';
    if (reason === 'document_not_found') return '未找到文档或文档已被删除';
    if (reason === 'empty_content_or_not_available') return '文档内容为空或不可获取，无法生成图谱';
    if (reason === 'no_significant_cooccurrence') return '未检测到足够的词共现关系，无法生成图谱';
    if (reason === 'fallback_disabled') return '图谱生成已禁用';
    if (reason.startsWith('error:')) return '系统错误：' + reason.replace('error:', '');
    return '图谱不可用';
};

const typeGuess = (n) => {
  const t = (n.type || '').toLowerCase();
  if (t.includes('person') || t.includes('user')) return '人';
  if (t.includes('org') || t.includes('company') || t.includes('team')) return '组织';
  if (t.includes('event') || t.includes('incident')) return '事件';
  if (t.includes('doc') || t.includes('file') || t.includes('page')) return '文档';
  if (t.includes('asset') || t.includes('resource')) return '资产';
  return '文档';
}

const assignTypesFromAttributes = () => {
  Object.keys(graphNodes.value || {}).forEach(id => {
    const n = graphNodes.value[id];
    if (!n.type) n.type = typeGuess(n);
  });
}

const rebuildFilterFromGraph = () => {
  const typesPresent = new Set();
  Object.values(graphNodes.value || {}).forEach(n => {
    const t = n.type || typeGuess(n);
    if (t) typesPresent.add(t);
  });
  const ordered = Array.from(typesPresent).sort((a,b) => {
    const ia = knownTypeOrder.indexOf(a);
    const ib = knownTypeOrder.indexOf(b);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return a.localeCompare(b, 'zh-CN');
  });
  const cmap = {};
  ordered.forEach(t => {
    const col = baseColorMap[t] || "#6b7280";
    cmap[t] = col;
  });
  colorMap.value = cmap;
  hiddenTypes.value = hiddenTypes.value.filter(t => typesPresent.has(t));
}

// Chat Methods
const fetchChatHistory = async (docId) => {
    if (!docId) return;
    
    // Safety check: Prevent fetching mixed history when no session is selected
    if (!currentSessionId.value) {
        console.log('Skipping history fetch: No session ID selected');
        chatMessages.value = [];
        return;
    }

    try {
        const params = {};
        if (currentSessionId.value) {
            params.session_id = currentSessionId.value;
        }
        const res = await api.get(`/knowledge/${docId}/qa/history`, { params });
        console.log(`[fetchChatHistory] Got ${res.data.length} messages.`);
        
        chatMessages.value = res.data;
        
        setTimeout(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }, 100);
    } catch (e) {
        console.error('Failed to fetch chat history:', e);
    }
};

const handleSuggestion = (text) => {
    if (chatLoading.value) return;
    chatInput.value = text;
    sendChatMessage();
};

const sendChatMessage = async () => {
    if (chatLoading.value) return;
    if (!chatInput.value.trim()) return;
    
    const query = chatInput.value;
    
    // Auto-create session ID if not exists (for the first message in a new context)
    if (!currentSessionId.value) {
        currentSessionId.value = generateUUID();
    }

    chatMessages.value.push({ role: 'user', content: query });
    chatInput.value = '';
    chatLoading.value = true;
    
    // Create placeholder for assistant message
    const assistantMsg = { 
        role: 'assistant', 
        content: '', 
        sources: [] 
    };
    chatMessages.value.push(assistantMsg);
    
    setTimeout(() => {
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }, 100);
    
    try {
        // Construct history (simplified)
        const history = chatMessages.value.slice(0, -2).map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`);
        
        // Prepare payload
        const payload = { 
            query, 
            history,
            scope: props.docId ? graphScope.value : 'global',
            session_id: currentSessionId.value
        };
        
        const url = props.docId 
            ? `/api/v1/knowledge/${props.docId}/qa` 
            : `/api/v1/knowledge/qa`;

        // Use fetch for streaming
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Add auth token if needed, usually managed by browser cookie or added manually
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            // Update message content in real-time
            assistantMsg.content = buffer;
            
            // Auto scroll
            if (chatContainer.value) {
                chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
            }
        }
        
        // Final update
        assistantMsg.content = buffer;
        
        // Refresh session list if this was the first message
        if (chatMessages.value.length <= 2 && showHistoryPanel.value) {
            fetchSessions();
        }
        
    } catch (e) {
        console.error(e);
        assistantMsg.content += `\n[Error: ${e.message}]`;
    } finally {
        chatLoading.value = false;
        setTimeout(() => {
            if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }, 100);
    }
};

const confirmClearChatHistory = () => {
    Modal.confirm({
        title: '开启新会话？',
        icon: createVNode(ExclamationCircleOutlined),
        content: '这将开启一个新的空白会话，旧的记录将保留在历史中。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                // Generate new session ID
                currentSessionId.value = generateUUID();
                chatMessages.value = [];
                message.success('新会话已开启');
                fetchSessions(); // Refresh list if panel is open
            } catch (e) {
                message.error('操作失败：' + (e.message));
            }
        }
    });
};

// Markdown & Citations
const renderMarkdown = (content, hasStructuredSources = false) => {
    if (!content) return '';
    try {
        let inputText = (content || '').trim();
        
        // 1. Handle <think> tags
        const thinkMatch = inputText.match(/<think>([\s\S]*?)<\/think>/);
        let thinkHtml = '';
        if (thinkMatch) {
            const thinkContent = thinkMatch[1];
            // Render think content as markdown too
            const parsedThink = marked.parse(thinkContent);
            thinkHtml = `
            <details class="mb-3 bg-amber-50/50 rounded-lg border border-amber-100 overflow-hidden group" ${inputText.includes('</think>') ? '' : 'open'}>
                <summary class="px-3 py-1.5 text-xs font-medium text-amber-600/70 cursor-pointer hover:bg-amber-50 flex items-center gap-2 select-none transition-colors">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                    思考过程
                </summary>
                <div class="px-3 py-2 text-xs text-slate-600 border-t border-amber-100/50 bg-white/50 leading-relaxed">
                    ${parsedThink}
                </div>
            </details>`;
            
            // Remove think block from main text to render answer separately
            inputText = inputText.replace(/<think>[\s\S]*?<\/think>/, '').trim();
        }

        inputText = inputText.replace(/^(\s*)\*\*([^*]+)\*\*([:：])/gm, '$1**$2** $3');
        inputText = inputText.replace(/\[\[Entity:\s*(.*?)\]\]/g, '<span class="entity-citation" data-entity="$1">$1</span>');
        inputText = inputText.replace(/doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?/gi, '');
        
        // Clean up sources format if needed
        if (hasStructuredSources) {
            const refHeaderPattern = /\n+\s*(?:#+\s*)?(?:\*\*)?(References|Sources|参考来源|引用|引用文献|Reference Document List)(:|\：)?(?:\*\*)?\s*(\n+|$)/gi;
            inputText = inputText.split(refHeaderPattern)[0];
        }
        
        inputText = inputText.replace(/\[+[\s\t]*(?:Source:[\s\t]*)?(\d+)[\s\t]*\]+/gi, '[$1]');
        inputText = inputText.replace(/\n{3,}/g, '\n\n').trim();
        inputText = inputText.replace(/\[(\d+)\]/g, (match, num) => {
            return `<span class="citation-icon" data-idx="${parseInt(num)-1}" title="点击在图谱中定位">${match}</span>`;
        });
        
        const answerHtml = marked.parse(inputText);
        return thinkHtml + answerHtml;
    } catch (e) {
        console.error('Markdown parse error:', e);
        return content;
    }
};

const handleCitationClick = (e, msg) => {
    const target = e.target;
    if (target && target.classList.contains('citation-icon')) {
        const idx = parseInt(target.getAttribute('data-idx') || '-1');
        if (idx >= 0 && msg.sources && msg.sources[idx]) {
            locateCitationInGraph(msg.sources[idx]);
        }
    }
};

const locateCitationInGraph = (source) => {
    if (!source) return;
    if (source.source === 'graph') {
        const entityName = source.title; 
        if (!graphNodes.value) return;
        const matchingNodeId = Object.keys(graphNodes.value).find(id => {
            const node = graphNodes.value[id];
            return (node.name === entityName) || (id === entityName);
        });
        if (matchingNodeId) {
            if (graphViewerRef.value) {
                graphViewerRef.value.focusNode(matchingNodeId);
                message.success(`已定位实体: ${entityName}`);
            }
            return;
        }
    }
    const content = source.content || '';
    if (!graphNodes.value) return;
    const matchingNodeIds = Object.keys(graphNodes.value).filter(id => {
        const node = graphNodes.value[id];
        const name = node.name || id;
        return content.includes(name);
    });
    if (matchingNodeIds.length > 0) {
        const targetNodeId = matchingNodeIds[0];
        if (graphViewerRef.value) {
            graphViewerRef.value.focusNode(targetNodeId);
            const nodeName = graphNodes.value[targetNodeId].name || targetNodeId;
            message.success(`已定位相关实体: ${nodeName}`);
        }
    } else {
        message.info('未在当前可见图谱中找到相关实体');
    }
};

const getUniqueDocs = (sources) => {
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
    return Array.from(docs.values()).sort((a, b) => b.score - a.score);
};

const getChunks = (sources) => {
    return (sources || []).filter(s => s.source === 'vector');
};

const getEntities = (sources) => {
    return (sources || []).filter(s => s.source === 'graph');
};
</script>

<style scoped>
/* Same styles as in KnowledgeBase.vue */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #e5e6eb;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #c9cdd4;
}

.animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    100% {
        transform: translateX(100%);
    }
}

.graph-skeleton {
    position: relative;
    overflow: hidden;
}

.graph-skeleton::after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    transform: translateX(-100%);
    background-image: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0) 0,
        rgba(255, 255, 255, 0.4) 20%,
        rgba(255, 255, 255, 0.7) 60%,
        rgba(255, 255, 255, 0)
    );
    animation: shimmer 2s infinite;
}

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
    color: #1e293b;
}
.markdown-content :deep(.entity-citation) {
    color: #2563eb;
    background-color: #eff6ff;
    padding: 0px 4px;
    border-radius: 4px;
    border-bottom: 1px dashed #3b82f6;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}
.markdown-content :deep(.entity-citation:hover) {
    background-color: #dbeafe;
    border-bottom-style: solid;
}
.markdown-content :deep(.citation-icon) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    background-color: #f1f5f9;
    color: #3b82f6;
    border: 1px solid #dbeafe;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 700;
    margin: 0 2px;
    padding: 0 3px;
    cursor: pointer;
    vertical-align: super;
    transition: all 0.2s;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.markdown-content :deep(.citation-icon:hover) {
    background-color: #3b82f6;
    border-color: #3b82f6;
    color: white;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}
</style>