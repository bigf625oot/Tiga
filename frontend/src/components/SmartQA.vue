<template>
  <div class="h-full flex bg-slate-50 overflow-hidden rounded-2xl shadow-sm border border-slate-200">
    <!-- Sidebar: Sessions -->
    <div class="w-64 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
        <div class="p-4 border-b border-slate-100">
            <button 
                @click="createNewSession" 
                class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl flex items-center justify-center gap-2 transition-colors shadow-sm shadow-blue-200 font-medium text-sm"
            >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                <span>新建对话</span>
            </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
            <div v-if="sessions.length === 0" class="text-center text-slate-400 text-xs py-8">
                暂无历史对话
            </div>
            <div 
                v-for="session in sessions" 
                :key="session.id"
                @click="selectSession(session)"
                class="group px-3 py-3 rounded-xl cursor-pointer flex items-center justify-between transition-all duration-200"
                :class="currentSessionId === session.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50 text-slate-600'"
            >
                <div class="flex items-center gap-3 overflow-hidden">
                    <svg class="w-4 h-4 flex-shrink-0" :class="currentSessionId === session.id ? 'text-blue-500' : 'text-slate-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                    <span class="text-sm truncate">{{ session.title || '新对话' }}</span>
                </div>
                <button 
                    @click.stop="deleteSession(session.id)"
                    class="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 rounded transition-opacity"
                >
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>
        </div>
    </div>

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-white relative">
        
        <!-- Header (Only show when chatting) -->
        <div v-if="messages.length > 0" class="px-6 py-3 border-b border-slate-100 flex justify-between items-center bg-white/80 backdrop-blur-sm z-10">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
                    <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                <div>
                    <h2 class="font-bold text-slate-800 text-sm">
                        {{ currentSession?.title || '智能问答助手' }}
                    </h2>
                    <div class="flex items-center gap-1 text-xs text-slate-500" v-if="currentAgent">
                        <span>当前智能体:</span>
                        <span class="font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">{{ currentAgent.name }}</span>
                    </div>
                </div>
            </div>
            
            <!-- Agent Selector -->
            <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500">选择智能体:</span>
                <select 
                    v-model="selectedAgentId" 
                    @change="handleAgentChange"
                    class="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none min-w-[150px]"
                    :disabled="isLoading || messages.length > 0"
                >
                    <option value="">默认问答助手</option>
                    <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                        {{ agent.name }}
                    </option>
                </select>
            </div>
        </div>

        <!-- Welcome / Empty State (Design Implementation) -->
        <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center p-8 bg-white overflow-y-auto">
             <div class="frame1321317936">
                <p class="text-heading">今天想说什么</p>
                <div class="frame367 relative group transition-all focus-within:ring-2 focus-within:ring-blue-100">
                    <textarea 
                        v-model="input" 
                        @keydown.enter.prevent="sendMessage"
                        class="text2 w-full h-full resize-none outline-none bg-transparent placeholder-slate-300" 
                        placeholder="描述您需要帮助的内容..."
                    ></textarea>
                    
                    <div class="frame374 absolute bottom-3 right-3 left-3 flex justify-between items-center">
                         <div class="frame1321315582 cursor-pointer hover:bg-slate-50 rounded-lg p-1 transition-colors">
                            <div class="frame flex items-center gap-2">
                                <svg class="icons w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
                                <p class="text3 text-slate-500 text-xs">附件</p>
                            </div>
                         </div>
                         
                         <div class="flex items-center gap-4">
                             <!-- Agent Selector Pill -->
                             <div class="frame1321318053 cursor-pointer flex items-center gap-1 px-2 py-1 rounded-full bg-slate-50 hover:bg-slate-100 transition-colors border border-slate-200">
                                <svg class="group w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                <select 
                                    v-model="selectedAgentId" 
                                    @change="handleAgentChange"
                                    class="text3 text-slate-700 bg-transparent outline-none cursor-pointer appearance-none pr-4 text-xs font-medium"
                                >
                                    <option value="">默认助手</option>
                                    <option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.name }}</option>
                                </select>
                             </div>
                             
                             <div class="frame1321315581 flex items-center gap-2">
                                <button @click="sendMessage" class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-md transition-all active:scale-95" :disabled="!input.trim()">
                                    <svg class="icons3 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"></path></svg>
                                </button>
                             </div>
                         </div>
                    </div>
                </div>

                <div class="frame1 mt-8">
                    <div class="frame3 cursor-pointer hover:bg-slate-50 transition-colors" @click="sendQuickMessage('分析最近的新闻报道')">
                        <svg class="icons4 w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
                        <p class="text4">分析新闻报道</p>
                    </div>
                    <div class="frame3 cursor-pointer hover:bg-slate-50 transition-colors" @click="sendQuickMessage('比较不同产品的优缺点')">
                        <svg class="icons4 w-4 h-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        <p class="text4">比较产品</p>
                    </div>
                    <div class="frame3 cursor-pointer hover:bg-slate-50 transition-colors" @click="sendQuickMessage('帮我查找附近的最佳面包店')">
                        <svg class="icons4 w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        <p class="text4">查找最佳面包店地图</p>
                    </div>
                    <div class="frame3 cursor-pointer hover:bg-slate-50 transition-colors" @click="sendQuickMessage('研究当前行业的最新趋势')">
                        <svg class="icons4 w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
                        <p class="text4">研究行业趋势</p>
                    </div>
                </div>
             </div>
        </div>

        <!-- Messages List (Standard Chat) -->
        <div v-else class="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" 
                 :class="['flex gap-4 max-w-4xl mx-auto', msg.role === 'user' ? 'flex-row-reverse' : '']">
                <!-- Avatar -->
                <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                     :class="msg.role === 'user' ? 'bg-blue-600' : 'bg-white border border-slate-200'">
                     <span v-if="msg.role === 'user'" class="text-white text-xs font-bold">Me</span>
                     <svg v-else class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                
                <!-- Content -->
                <div :class="['rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed max-w-[85%]', 
                              msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white border border-slate-100 text-slate-700 rounded-tl-sm']">
                    <div v-if="msg.role === 'assistant'">
                        <!-- Thinking Block -->
                        <div v-if="msg.reasoning || (msg.meta_data && msg.meta_data.reasoning)" 
                             class="mb-3 p-3 bg-slate-50 border-l-4 border-indigo-200 rounded text-xs text-slate-500 font-mono whitespace-pre-wrap">
                            <div class="flex items-center gap-1 mb-1 text-indigo-400 font-semibold uppercase tracking-wider">
                                <svg class="w-3 h-3 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                                Thinking Process
                            </div>
                            {{ msg.reasoning || msg.meta_data.reasoning }}
                        </div>
                        
                        <!-- Amis Renderer (for Charts) -->
                        <div v-if="isAmisJSON(msg.content)" class="amis-container my-2 border border-slate-200 rounded-lg overflow-hidden">
                            <div :id="'amis-' + index"></div>
                        </div>
                        
                        <!-- Markdown Content -->
                        <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                    </div>
                    <div v-else>{{ msg.content }}</div>
                </div>
            </div>

            <!-- Loading Indicator -->
            <div v-if="isLoading && !isStreaming" class="flex gap-4 max-w-4xl mx-auto">
                 <div class="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 shadow-sm">
                     <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path></svg>
                 </div>
                 <div class="bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm flex items-center gap-2">
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></span>
                 </div>
            </div>
        </div>

        <!-- Input Area (Bottom - Only show when chatting) -->
        <div class="p-4 bg-white border-t border-slate-100 z-10" v-if="currentSessionId && messages.length > 0">
            <div class="max-w-4xl mx-auto relative">
                <textarea 
                  v-model="input" 
                  @keydown.enter.prevent="sendMessage"
                  rows="1"
                  placeholder="输入您的问题，按 Enter 发送..." 
                  class="w-full pl-4 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none resize-none text-sm text-slate-700 placeholder-slate-400 transition-all shadow-inner"
                  :disabled="isLoading"
                  style="min-height: 52px; max-height: 120px;"
                  @input="adjustHeight"
                ></textarea>
                <button 
                  @click="sendMessage"
                  class="absolute right-2 bottom-2 p-2 rounded-lg transition-all duration-200"
                  :class="input.trim() && !isLoading ? 'bg-blue-600 text-white shadow-lg shadow-blue-200 hover:bg-blue-700' : 'bg-slate-200 text-slate-400 cursor-not-allowed'"
                  :disabled="isLoading || !input.trim()"
                >
                    <svg class="w-5 h-5 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
                </button>
            </div>
            <p class="text-center text-[10px] text-slate-400 mt-2">内容由 AI 生成，仅供参考</p>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed, watch, createVNode } from 'vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Modal } from 'ant-design-vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';

const input = ref('');
const messages = ref([]);
const sessions = ref([]);
const agents = ref([]);
const currentSessionId = ref(null);
const selectedAgentId = ref('');
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);

const currentSession = computed(() => sessions.value.find(s => s.id === currentSessionId.value));
const currentAgent = computed(() => agents.value.find(a => a.id === selectedAgentId.value));

onMounted(() => {
    fetchAgents();
    fetchSessions();
});

const adjustHeight = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
};

const sendQuickMessage = (text) => {
    input.value = text;
    sendMessage();
};

// API Helpers
const fetchAgents = async () => {
    try {
        const res = await fetch('/api/v1/agents/');
        if (res.ok) {
            agents.value = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch agents", e);
    }
};

const fetchSessions = async () => {
    try {
        const res = await fetch('/api/v1/chat/sessions');
        if (res.ok) {
            sessions.value = await res.json();
            // Select first session if exists and none selected
            if (sessions.value.length > 0 && !currentSessionId.value) {
                selectSession(sessions.value[0]);
            }
        }
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    }
};

const selectSession = async (session) => {
    currentSessionId.value = session.id;
    selectedAgentId.value = session.agent_id || '';
    
    // Fetch details (messages)
    try {
        const res = await fetch(`/api/v1/chat/sessions/${session.id}`);
        if (res.ok) {
            const data = await res.json();
            messages.value = data.messages || [];
            scrollToBottom();
            
            // Render Amis charts if any
            nextTick(() => {
                messages.value.forEach((msg, idx) => {
                    if (msg.role === 'assistant' && isAmisJSON(msg.content)) {
                        renderAmis(idx, msg.content);
                    }
                });
            });
        }
    } catch (e) {
        console.error("Failed to fetch session details", e);
    }
};

const createNewSession = async () => {
    try {
        const res = await fetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                title: '新对话',
                agent_id: selectedAgentId.value || null 
            })
        });
        if (res.ok) {
            const newSession = await res.json();
            sessions.value.unshift(newSession);
            selectSession(newSession);
        }
    } catch (e) {
        console.error("Failed to create session", e);
    }
};

const deleteSession = (id) => {
    Modal.confirm({
        title: '确定要删除此对话吗？',
        icon: createVNode(ExclamationCircleOutlined),
        content: '删除后将无法恢复，请谨慎操作。',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
            try {
                const res = await fetch(`/api/v1/chat/sessions/${id}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    sessions.value = sessions.value.filter(s => s.id !== id);
                    if (currentSessionId.value === id) {
                        currentSessionId.value = null;
                        messages.value = [];
                        // If there are other sessions, select the first one
                        if (sessions.value.length > 0) {
                            selectSession(sessions.value[0]);
                        } else {
                            // Reset agent selection if no sessions left
                            selectedAgentId.value = '';
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to delete session", e);
            }
        }
    });
};

const handleAgentChange = async () => {
    // If we have an empty session selected, update its agent immediately
    if (messages.value.length === 0 && currentSessionId.value) {
        try {
            console.log("Updating session agent:", currentSessionId.value, selectedAgentId.value);
            const res = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: selectedAgentId.value || null })
            });
            if (!res.ok) throw new Error(res.statusText);
            
            // Update local session list if needed (though agent_id isn't displayed in list usually)
            const sess = sessions.value.find(s => s.id === currentSessionId.value);
            if (sess) sess.agent_id = selectedAgentId.value;
        } catch (e) {
            console.error("Failed to update session agent", e);
        }
    }
};

const sendMessage = async () => {
    if (!input.value.trim() || isLoading.value) return;
    
    // Auto-create session if none exists
    if (!currentSessionId.value) {
        try {
            const res = await fetch('/api/v1/chat/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    title: input.value.slice(0, 20) || '新对话',
                    agent_id: selectedAgentId.value || null 
                })
            });
            if (res.ok) {
                const newSession = await res.json();
                sessions.value.unshift(newSession);
                currentSessionId.value = newSession.id;
            } else {
                throw new Error("Failed to create session");
            }
        } catch (e) {
            console.error(e);
            return;
        }
    }
    
    const userMsg = input.value;
    input.value = '';
    const textarea = document.querySelector('textarea');
    if (textarea) textarea.style.height = 'auto';

    messages.value.push({ role: 'user', content: userMsg });
    isLoading.value = true;
    isStreaming.value = false;
    
    scrollToBottom();
    
    try {
        const response = await fetch(`/api/v1/chat/sessions/${currentSessionId.value}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMsg })
        });
        
        if (!response.ok) throw new Error(response.statusText);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        messages.value.push({ role: 'assistant', content: '', reasoning: '' });
        const assistantMsg = messages.value[messages.value.length - 1];
        const assistantMsgIndex = messages.value.length - 1;
        
        isStreaming.value = true;
        
        let fullBuffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            fullBuffer += chunk;
            
            // Streaming parse logic
            const thinkStart = fullBuffer.indexOf('<think>');
            
            if (thinkStart !== -1) {
                const thinkEnd = fullBuffer.indexOf('</think>');
                if (thinkEnd !== -1) {
                    assistantMsg.reasoning = fullBuffer.substring(thinkStart + 7, thinkEnd).trim();
                    const beforeThink = fullBuffer.substring(0, thinkStart);
                    const afterThink = fullBuffer.substring(thinkEnd + 8);
                    assistantMsg.content = (beforeThink + afterThink).trim();
                } else {
                    assistantMsg.reasoning = fullBuffer.substring(thinkStart + 7);
                    assistantMsg.content = fullBuffer.substring(0, thinkStart);
                }
            } else {
                assistantMsg.content = fullBuffer;
            }
            
            scrollToBottom();
        }
        
        if (isAmisJSON(assistantMsg.content)) {
            nextTick(() => renderAmis(assistantMsgIndex, assistantMsg.content));
        }
        
    } catch (e) {
        console.error(e);
        messages.value.push({ role: 'assistant', content: "Error: " + e.message });
    } finally {
        isLoading.value = false;
        isStreaming.value = false;
        scrollToBottom();
    }
};

const scrollToBottom = () => {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
    });
};

const renderMarkdown = (text) => {
    try {
        let html = marked.parse(text || '');
        html = html.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, open, formula) => {
            try { return katex.renderToString(formula, { displayMode: true }); } catch { return match; }
        });
        html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try { return katex.renderToString(formula, { displayMode: false }); } catch { return match; }
        });
        return html;
    } catch (e) {
        return text;
    }
};

const isAmisJSON = (text) => {
    if (!text || !text.trim().startsWith('```json')) return false;
    return text.includes('"type": "page"') || text.includes('"type": "chart"');
};

const renderAmis = (index, content) => {
    const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
    if (jsonMatch && jsonMatch[1]) {
        try {
            const schema = JSON.parse(jsonMatch[1]);
            const container = document.getElementById('amis-' + index);
            if (container && window.amis) {
                window.amis.embed(container, schema);
            }
        } catch (e) {
            console.error("Amis render error", e);
        }
    }
};

</script>

<style scoped>
/* Frame 1321317936 Styles */
.frame1321317936 {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 800px;
  row-gap: 24px;
}

.text-heading {
  padding: 24px 0;
  width: 100%;
  text-align: center;
  line-height: 36px;
  color: #2a2f3c;
  font-family: "PingFang SC", sans-serif;
  font-size: 28px;
  font-weight: 500;
}

.frame367 {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  align-self: stretch;
  justify-content: space-between;
  border: 1px solid #e5e6eb;
  border-radius: 16px;
  box-shadow: 0px 4px 24px 0px #bfcded33;
  background: #ffffff;
  padding: 16px;
  height: 140px;
}

.text2 {
  font-size: 15px;
  line-height: 1.6;
  color: #1e293b;
}

.frame1 {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.frame3 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  column-gap: 8px;
  border-radius: 100px;
  padding: 8px 16px;
  background: #f8fafc;
  border: 1px solid transparent;
}
.frame3:hover {
    border-color: #e2e8f0;
    background: #f1f5f9;
}

.text4 {
  line-height: 18px;
  color: #2a2f3c;
  font-size: 12px;
}

.markdown-body {
    font-size: 14px;
    line-height: 1.6;
    color: #334155;
}
/* Typography */
.markdown-body p { margin-bottom: 0.75em; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body strong { font-weight: 600; color: #1e293b; }
.markdown-body em { font-style: italic; }
/* Headings */
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
    font-weight: 600;
    color: #0f172a;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    line-height: 1.3;
}
.markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3em; }
.markdown-body h2 { font-size: 1.3em; }
.markdown-body h3 { font-size: 1.1em; }
/* Lists */
.markdown-body ul, .markdown-body ol { padding-left: 1.5em; margin-bottom: 0.75em; }
.markdown-body ul { list-style-type: disc; }
.markdown-body ol { list-style-type: decimal; }
/* Code */
.markdown-body pre { background: #f1f5f9; padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 1em; border: 1px solid #e2e8f0; }
.markdown-body code { font-family: monospace; background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-size: 0.9em; }
</style>