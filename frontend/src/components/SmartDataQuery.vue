<template>
  <div class="h-full flex bg-white overflow-hidden rounded-2xl shadow-sm border border-slate-200">
    <!-- Config Sidebar -->
    <div class="w-96 bg-white border-r border-slate-200 flex flex-col flex-shrink-0 p-6 overflow-y-auto custom-scrollbar">
        <h2 class="text-lg font-bold mb-6 flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
            数据库配置
        </h2>
        
        <a-form 
            ref="formRef"
            :model="config" 
            :rules="rules"
            layout="vertical" 
            class="space-y-4"
        >
            <a-form-item label="数据库类型" name="type">
                <a-select v-model:value="config.type" @change="handleTypeChange">
                    <a-select-option value="sqlite">SQLite</a-select-option>
                    <a-select-option value="postgresql">PostgreSQL</a-select-option>
                    <a-select-option value="mysql">MySQL</a-select-option>
                </a-select>
            </a-form-item>
            
            <template v-if="config.type === 'sqlite'">
                <a-form-item label="文件路径" name="path" help="请输入SQLite数据库文件的绝对路径">
                    <a-input v-model:value="config.path" placeholder="e.g. C:/data/app.db" />
                </a-form-item>
            </template>
            
            <template v-else>
                <div class="grid grid-cols-3 gap-3">
                    <div class="col-span-2">
                        <a-form-item label="主机地址" name="host">
                            <a-input v-model:value="config.host" placeholder="localhost" />
                        </a-form-item>
                    </div>
                    <div>
                        <a-form-item label="端口" name="port">
                            <a-input-number v-model:value="config.port" class="w-full" :controls="false" />
                        </a-form-item>
                    </div>
                </div>
                
                <a-form-item label="用户名" name="user">
                    <a-input v-model:value="config.user" placeholder="root" />
                </a-form-item>
                
                <a-form-item label="密码" name="password">
                    <a-input-password v-model:value="config.password" placeholder="请输入密码" />
                </a-form-item>

                <!-- Advanced Options Toggle -->
                <div class="pt-2">
                    <div 
                        @click="showAdvanced = !showAdvanced" 
                        class="flex items-center gap-1 text-xs text-blue-600 cursor-pointer hover:text-blue-700 select-none font-medium"
                    >
                        <span>更多连接配置</span>
                        <svg class="w-3 h-3 transition-transform duration-200" :class="showAdvanced ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </div>
                    
                    <div v-show="showAdvanced" class="mt-4 space-y-4 p-4 bg-slate-50 rounded-xl border border-slate-100 animate-in fade-in slide-in-from-top-2 duration-200">
                        <a-form-item label="数据库名称" name="database">
                            <a-input v-model:value="config.database" placeholder="选填，默认连接postgres/mysql" />
                        </a-form-item>
                        
                        <div class="grid grid-cols-2 gap-3">
                            <a-form-item label="连接超时 (秒)" name="timeout">
                                <a-input-number v-model:value="config.timeout" class="w-full" :min="1" />
                            </a-form-item>
                            
                            <a-form-item label="连接池大小" name="pool_size">
                                <a-input-number v-model:value="config.pool_size" class="w-full" :min="1" />
                            </a-form-item>
                        </div>
                        
                        <a-form-item v-if="config.type === 'mysql'" label="字符集" name="charset">
                            <a-select v-model:value="config.charset">
                                <a-select-option value="utf8mb4">utf8mb4</a-select-option>
                                <a-select-option value="utf8">utf8</a-select-option>
                                <a-select-option value="latin1">latin1</a-select-option>
                            </a-select>
                        </a-form-item>
                        
                        <a-form-item v-if="config.type === 'postgresql'" label="SSL 模式" name="ssl_mode">
                            <a-select v-model:value="config.ssl_mode">
                                <a-select-option value="disable">Disable</a-select-option>
                                <a-select-option value="require">Require</a-select-option>
                                <a-select-option value="verify-ca">Verify CA</a-select-option>
                                <a-select-option value="verify-full">Verify Full</a-select-option>
                            </a-select>
                        </a-form-item>
                    </div>
                </div>
            </template>
            
            <div class="flex flex-col gap-3 pt-4 border-t border-slate-100 mt-4">
                <a-button @click="testConnection" :loading="testing" class="w-full" :disabled="connecting">
                    <template #icon>
                        <svg class="w-4 h-4 mr-2 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    </template>
                    测试连接
                </a-button>
                
                <a-button type="primary" @click="saveAndConnect" :loading="connecting" class="w-full h-10 font-medium bg-blue-600" :disabled="testing">
                    保存配置并连接
                </a-button>
            </div>
        </a-form>
        
        <!-- Status Messages -->
        <div v-if="testResult" class="mt-4 p-3 rounded-lg text-xs flex items-start gap-2" :class="testResult.success ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'">
            <component :is="testResult.success ? 'CheckCircleOutlined' : 'CloseCircleOutlined'" class="mt-0.5" />
            <span class="break-all">{{ testResult.message }}</span>
        </div>
        
        <div class="mt-8 p-4 bg-blue-50 text-blue-700 text-xs rounded-xl border border-blue-100 leading-relaxed">
            <p class="font-bold mb-2 flex items-center gap-1">
                <InfoCircleOutlined /> 使用提示
            </p>
            <p>连接成功后，您可以直接使用自然语言查询数据。</p>
            <p class="mt-2 font-medium">示例指令：</p>
            <ul class="list-disc pl-4 mt-1 space-y-1 text-blue-600">
                <li>"查询最近10笔销售记录"</li>
                <li>"统计各类目的销售总额"</li>
                <li>"绘制月度销售趋势图"</li>
            </ul>
        </div>
    </div>
    
    <!-- Chat Area -->
    <div class="flex-1 flex flex-col h-full bg-white relative">
        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6" ref="messagesContainer">
             <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400">
                <div class="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-sm mb-6 border border-slate-100">
                    <svg class="w-10 h-10 text-blue-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
                </div>
                <h3 class="text-lg font-semibold text-slate-700 mb-2">智能问数助手</h3>
                <p class="text-sm max-w-xs text-center leading-relaxed">配置数据库并开始提问，我会自动为您生成 SQL 查询并可视化结果。</p>
             </div>
             
             <div v-for="(msg, index) in messages" :key="index" 
                 :class="['flex gap-4 max-w-4xl mx-auto', msg.role === 'user' ? 'flex-row-reverse' : '']">
                <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                     :class="msg.role === 'user' ? 'bg-blue-600' : 'bg-white border border-slate-200'">
                     <span v-if="msg.role === 'user'" class="text-white text-xs font-bold">Me</span>
                     <svg v-else class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                <div :class="['rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed max-w-[85%]', 
                              msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-slate-50 border border-slate-100 text-slate-700 rounded-tl-sm']">
                    <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                    <div v-else>{{ msg.content }}</div>
                </div>
            </div>
            
            <!-- Loading -->
            <div v-if="isLoading && !isStreaming" class="flex gap-4 max-w-4xl mx-auto">
                 <div class="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 shadow-sm">
                     <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                 </div>
                 <div class="bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm flex items-center gap-2">
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
                    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></span>
                 </div>
            </div>
        </div>
        
        <!-- Input -->
        <div class="p-4 bg-white border-t border-slate-100 z-10">
            <div class="max-w-4xl mx-auto relative">
                <textarea 
                  v-model="input" 
                  @keydown.enter.exact.prevent="sendMessage"
                  rows="3"
                  placeholder="输入您的问题..." 
                  class="w-full pl-4 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none resize-none text-sm text-slate-700 placeholder-slate-400 transition-all shadow-inner"
                  :disabled="isLoading"
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
            <p class="text-center text-[10px] text-slate-400 mt-2">智能问数 · Vanna AI 驱动</p>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { marked } from 'marked';
import { CheckCircleOutlined, CloseCircleOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';

const formRef = ref();
const config = ref({
    type: 'sqlite',
    path: '',
    host: 'localhost',
    port: 5432,
    database: '',
    user: '',
    password: '',
    timeout: 30,
    pool_size: 5,
    charset: 'utf8mb4',
    ssl_mode: 'disable'
});

const showAdvanced = ref(false);
const testing = ref(false);
const connecting = ref(false);
const testResult = ref(null);
const input = ref('');
const messages = ref([]);
const isLoading = ref(false);
const isStreaming = ref(false);
const messagesContainer = ref(null);

const rules = {
    type: [{ required: true, message: '请选择数据库类型' }],
    path: [{ required: true, message: '请输入文件路径', trigger: 'blur' }],
    host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
    port: [{ required: true, message: '请输入端口号' }],
    user: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    // Password might be empty for some local setups, but generally required
    // Let's make it optional for now or depend on user intent
    database: [{ required: false }]
};

const handleTypeChange = (val) => {
    // Set default ports
    if (val === 'postgresql') config.value.port = 5432;
    if (val === 'mysql') config.value.port = 3306;
    if (val === 'sqlite') config.value.port = null;
    testResult.value = null;
};

const fetchConfig = async () => {
    try {
        const res = await fetch('/api/v1/data_query/config');
        if (res.ok) {
            const data = await res.json();
            if (Object.keys(data).length > 0) {
                config.value = { ...config.value, ...data };
            }
        }
    } catch (e) {
        console.error("Failed to load config", e);
    }
};

const testConnection = async () => {
    testResult.value = null;
    try {
        await formRef.value.validate();
    } catch (error) {
        return;
    }
    
    testing.value = true;
    try {
        const res = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (res.ok) {
            testResult.value = { success: true, message: '连接测试成功！' };
            message.success('连接测试成功');
        } else {
            const err = await res.json();
            testResult.value = { success: false, message: '连接失败: ' + (err.detail || '未知错误') };
            message.error('连接测试失败');
        }
    } catch (e) {
        testResult.value = { success: false, message: '网络错误: ' + e.message };
        message.error('连接测试失败');
    } finally {
        testing.value = false;
    }
};

const saveAndConnect = async () => {
    try {
        await formRef.value.validate();
    } catch (error) {
        return;
    }
    
    connecting.value = true;
    testResult.value = null;
    
    // 1. Connect
    try {
        const connRes = await fetch('/api/v1/data_query/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (!connRes.ok) {
            const err = await connRes.json();
            throw new Error(err.detail || '连接失败');
        }
        
        // 2. Save Config
        const saveRes = await fetch('/api/v1/data_query/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
        });
        
        if (!saveRes.ok) {
            message.warning('连接成功，但配置保存失败');
        } else {
            message.success('配置已保存并连接成功');
        }
        
        testResult.value = { success: true, message: '已连接并就绪' };
        
    } catch (e) {
        testResult.value = { success: false, message: e.message };
        message.error(e.message);
    } finally {
        connecting.value = false;
    }
};

const sendMessage = async () => {
    if (!input.value.trim() || isLoading.value) return;
    const userMsg = input.value;
    input.value = '';
    messages.value.push({ role: 'user', content: userMsg });
    isLoading.value = true;
    scrollToBottom();
    
    try {
        const response = await fetch('/api/v1/data_query/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userMsg })
        });
        
        if (!response.ok) throw new Error(response.statusText);
        
        messages.value.push({ role: 'assistant', content: '' });
        const assistantMsg = messages.value[messages.value.length - 1];
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        isStreaming.value = true;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            assistantMsg.content += chunk;
            scrollToBottom();
        }
        
    } catch (e) {
        messages.value.push({ role: 'assistant', content: 'Error: ' + e.message });
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
        let inputText = (text || '').trim();
        
        // [Cleanup] Remove raw document references like doc#3:xxxx...
        inputText = inputText.replace(/doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?/gi, '');
        
        // [Cleanup] Remove the trailing "References" or "Sources" section aggressively
        const refHeaderPattern = /\n+\s*(?:#+\s*)?(?:\*\*)?(References|Sources|参考来源|引用|引用文献|Reference Document List)(:|\：)?(\*\*)?\s*(\n+|$)/gi;
        inputText = inputText.split(refHeaderPattern)[0];

        // [Cleanup] Also remove any trailing lines that look like [n] or [n] something
        let lines = inputText.split('\n');
        while (lines.length > 0 && (/^\s*\[\d+\]\s*.*$/.test(lines[lines.length - 1]) || !lines[lines.length - 1].trim())) {
            lines.pop();
        }
        inputText = lines.join('\n');

        // [Cleanup] Trim multiple newlines
        inputText = inputText.replace(/\n{3,}/g, '\n\n');

        // [Fix] Handle cases where bold text at the start of a line (possibly indented) 
        // is followed by a colon, which can break some Markdown parsers (like marked).
        inputText = inputText.replace(/^(\s*)\*\*([^*]+)\*\*([:：])/gm, '$1**$2** $3');

        // [Fix] Handle multi-layered brackets like [[[1]]], [[ [1] ]], or [[Source: 1]]
        // Consolidate all citation patterns into a single unified format [n]
        inputText = inputText.replace(/\[+[\s\t]*(?:Source:[\s\t]*)?(\d+)[\s\t]*\]+/gi, '[$1]');

        return marked.parse(inputText);
    } catch (e) {
        console.error('Markdown parse error:', e);
        return text || '';
    }
};

onMounted(() => {
    fetchConfig();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

/* Markdown Styles */
.markdown-body :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
    font-size: 13px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
    border: 1px solid #e2e8f0;
    padding: 10px 14px;
}
.markdown-body :deep(th) {
    background-color: #f8fafc;
    font-weight: 600;
    text-align: left;
    color: #475569;
}
.markdown-body :deep(tr:nth-child(even)) {
    background-color: #fcfcfc;
}
.markdown-body :deep(tr:hover) {
    background-color: #f1f5f9;
}
.markdown-body :deep(pre) {
    background: #f1f5f9;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid #e2e8f0;
}
.markdown-body :deep(code) {
    font-family: 'Hack', monospace;
    font-size: 12px;
}
</style>
