<template>
  <div class="p-6 h-full overflow-y-auto">
    <div class="mb-6">
      <h2 class="text-lg font-bold text-slate-800 mb-2">OpenClaw 网关信息</h2>
      <p class="text-sm text-slate-500">网关的核心配置和状态信息。</p>
    </div>

    <div v-if="loading" class="flex justify-center py-10">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>

    <div v-else-if="error" class="bg-red-50/50 border border-red-100 rounded-xl p-6 flex flex-col items-center justify-center text-center">
      <div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <CloseCircleOutlined class="text-xl text-red-500" />
      </div>
      <h3 class="text-sm font-bold text-slate-800 mb-1">获取网关信息失败</h3>
      <p class="text-xs text-slate-500 mb-4 max-w-xs">{{ error }}</p>
      <button 
        @click="fetchInfo" 
        class="px-4 py-2 bg-white border border-slate-200 shadow-sm rounded-lg text-xs font-medium text-slate-600 hover:text-indigo-600 hover:border-indigo-200 transition-all"
      >
        重试连接
      </button>
    </div>

    <div v-else class="space-y-4">
      <!-- Status Card -->
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-slate-500">运行状态</span>
          <span 
            class="px-2 py-0.5 text-xs font-medium rounded-full"
            :class="info.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'"
          >
            {{ info.status === 'active' ? '运行中' : '离线' }}
          </span>
        </div>
        <div class="text-xs text-slate-400">版本: {{ info.version || '未知' }}</div>
      </div>

      <!-- Info Items -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="divide-y divide-slate-100">
          <div class="p-4">
            <div class="text-xs font-medium text-slate-500 mb-1">网关 URL</div>
            <div class="text-sm text-slate-800 font-mono break-all">{{ info.gateway_url || '未配置' }}</div>
          </div>
          
          <div class="p-4">
            <div class="text-xs font-medium text-slate-500 mb-1">WebSocket 地址</div>
            <div class="text-sm text-slate-800 font-mono break-all">{{ info.websocket_url || '不可用' }}</div>
          </div>

          <div class="p-4">
            <div class="text-xs font-medium text-slate-500 mb-1">网关令牌 (Token)</div>
            <div class="flex items-center gap-2">
               <div class="text-sm text-slate-800 font-mono break-all flex-1">
                 {{ showToken ? info.gateway_token : '•'.repeat(20) }}
               </div>
               <button @click="showToken = !showToken" class="text-indigo-600 hover:text-indigo-800 text-xs font-medium">
                 {{ showToken ? '隐藏' : '显示' }}
               </button>
            </div>
          </div>

          <div class="p-4">
            <div class="text-xs font-medium text-slate-500 mb-1">默认会话密钥 (Session Secret)</div>
            <div class="flex items-center gap-2">
               <div class="text-sm text-slate-800 font-mono break-all flex-1">
                 {{ showSecret ? info.session_secret : '•'.repeat(20) }}
               </div>
               <button @click="showSecret = !showSecret" class="text-indigo-600 hover:text-indigo-800 text-xs font-medium">
                 {{ showSecret ? '隐藏' : '显示' }}
               </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-4 flex justify-end">
        <button 
          @click="fetchInfo" 
          class="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 transition-colors"
        >
          <ReloadOutlined /> 刷新
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { ReloadOutlined, CloseCircleOutlined } from '@ant-design/icons-vue';

const info = ref<any>({});
const loading = ref(false);
const error = ref('');
const showToken = ref(false);
const showSecret = ref(false);

const fetchInfo = async () => {
  loading.value = true;
  error.value = '';
  try {
    const res = await fetch('/api/v1/openclaw/info');
    if (res.ok) {
      info.value = await res.json();
    } else {
      error.value = `API请求失败: ${res.status} ${res.statusText}`;
    }
  } catch (e) {
    error.value = '网络连接异常，无法连接到OpenClaw服务';
    console.error(e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchInfo();
});
</script>