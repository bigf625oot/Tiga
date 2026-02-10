<template>
  <a-drawer
    title="系统日志"
    placement="right"
    :width="600"
    :open="visible"
    @close="$emit('close')"
    :headerStyle="themeStyles.header"
    :bodyStyle="themeStyles.body"
    class="log-drawer"
    :rootClassName="isDarkMode ? 'log-drawer-dark' : 'log-drawer-light'"
  >
    <template #extra>
      <a-space>
        <button 
            @click="toggleTheme" 
            class="w-7 h-7 flex items-center justify-center rounded transition-colors mr-1 cursor-pointer"
            :class="isDarkMode ? 'text-slate-400 hover:text-amber-400 hover:bg-slate-800' : 'text-slate-500 hover:text-indigo-600 hover:bg-slate-100'"
            title="切换主题"
        >
            <component :is="isDarkMode ? 'Sunny' : 'Moon'" class="w-4 h-4" />
        </button>
        
        <a-button type="default" size="small" @click="downloadLogs" 
            :class="isDarkMode ? 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white hover:border-slate-600' : 'bg-white border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-200'"
            class="flex items-center gap-1"
        >
            <template #icon><DownloadOutlined /></template>
            下载
        </a-button>
        <a-button type="text" danger size="small" @click="$emit('clear')" class="flex items-center gap-1">
            <template #icon><DeleteOutlined /></template>
            清空
        </a-button>
      </a-space>
    </template>
    
    <div class="h-full flex flex-col font-mono text-xs transition-colors duration-300" :class="isDarkMode ? 'text-slate-300' : 'text-slate-600'">
      <!-- Toolbar -->
      <div class="flex items-center gap-3 p-4 border-b transition-all duration-300" 
           :class="isDarkMode ? 'border-slate-800/50 bg-slate-900/30 backdrop-blur-sm' : 'border-slate-100 bg-white/60 backdrop-blur-sm'">
          <a-input 
              v-model:value="searchQuery" 
              placeholder="搜索日志..." 
              size="small" 
              class="flex-1 tech-input"
              :class="{ 'tech-input-dark': isDarkMode }"
              allowClear
              :bordered="false"
          >
              <template #prefix>
                  <SearchOutlined :class="isDarkMode ? 'text-cyan-500/70' : 'text-slate-400'" />
              </template>
          </a-input>
          <a-select 
              v-model:value="filterLevel" 
              size="small" 
              class="w-28 tech-select"
              :class="{ 'tech-select-dark': isDarkMode }"
              :dropdownMatchSelectWidth="false"
              :bordered="false"
          >
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="info">
                <span :class="isDarkMode ? 'text-blue-400' : 'text-blue-600'">信息</span>
              </a-select-option>
              <a-select-option value="warning">
                <span :class="isDarkMode ? 'text-amber-400' : 'text-amber-600'">警告</span>
              </a-select-option>
              <a-select-option value="error">
                <span :class="isDarkMode ? 'text-red-400' : 'text-red-600'">错误</span>
              </a-select-option>
              <a-select-option value="success">
                <span :class="isDarkMode ? 'text-emerald-400' : 'text-emerald-600'">成功</span>
              </a-select-option>
          </a-select>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-1 custom-scrollbar" ref="logContainer">
         <EmptyLogState v-if="filteredLogs.length === 0" :isDarkMode="isDarkMode" />
         <div v-else v-for="(log, idx) in filteredLogs" :key="idx" 
              class="flex gap-2 p-1 rounded-md transition-colors group border border-transparent"
              :class="isDarkMode ? 'hover:bg-slate-800/80 hover:border-slate-800' : 'hover:bg-slate-100 hover:border-slate-200'"
         >
            <span class="shrink-0 select-none w-[85px] tabular-nums opacity-60">[{{ formatTime(log.timestamp) }}]</span>
            <span :class="getLevelClass(log.level)" class="shrink-0 w-12 uppercase font-bold text-[10px] pt-0.5 select-none text-center rounded-[3px]">{{ log.level }}</span>
            <span v-if="log.step" class="shrink-0 select-none font-medium" :class="isDarkMode ? 'text-indigo-400' : 'text-indigo-600'">[{{ log.step }}]</span>
            <span class="break-all whitespace-pre-wrap selection:bg-indigo-500/30 flex-1 leading-relaxed">{{ translateLog(log.message) }}</span>
         </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import dayjs from 'dayjs';
import { 
    DownloadOutlined, 
    DeleteOutlined,
    SearchOutlined
} from '@ant-design/icons-vue';
import EmptyLogState from '../common/EmptyLogState.vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  logs: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'clear']);
const logContainer = ref(null);
const isDarkMode = ref(true);

const searchQuery = ref('');
const filterLevel = ref('all');

const filteredLogs = computed(() => {
    let res = props.logs;
    if (filterLevel.value !== 'all') {
        res = res.filter(l => l.level === filterLevel.value);
    }
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        res = res.filter(l => l.message.toLowerCase().includes(q) || (l.step && l.step.toLowerCase().includes(q)));
    }
    return res;
});

const translateLog = (msg) => {
    if (!msg) return '';
    let text = msg;
    text = text.replace(/Retrieved (\d+) docs/i, '已检索到 $1 份文档');
    text = text.replace(/Next step: (.+)/i, '下一步计划: $1');
    text = text.replace(/Starting Dynamic Workflow/i, '开始动态工作流执行');
    text = text.replace(/Workflow finished/i, '工作流执行完成');
    text = text.replace(/Connection closed/i, '连接已关闭');
    return text;
};

const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value;
};

const themeStyles = computed(() => ({
    header: {
        padding: '16px 24px',
        borderBottom: isDarkMode.value ? '1px solid #1e293b' : '1px solid #e2e8f0',
        background: isDarkMode.value ? '#0f172a' : '#ffffff',
        color: isDarkMode.value ? '#f8fafc' : '#0f172a',
        transition: 'all 0.3s ease'
    },
    body: {
        padding: '0',
        backgroundColor: isDarkMode.value ? '#0f172a' : '#ffffff',
        transition: 'all 0.3s ease'
    }
}));

const formatTime = (ts) => dayjs(ts).format('HH:mm:ss.SSS');

const getLevelClass = (l) => {
    const level = l?.toLowerCase() || 'info';
    if (isDarkMode.value) {
        switch(level) {
            case 'error': return 'text-red-400 bg-red-950/30 border border-red-900/50';
            case 'warn':
            case 'warning': return 'text-amber-400 bg-amber-950/30 border border-amber-900/50';
            case 'success': return 'text-emerald-400 bg-emerald-950/30 border border-emerald-900/50';
            default: return 'text-blue-400 bg-blue-950/30 border border-blue-900/50';
        }
    } else {
        switch(level) {
            case 'error': return 'text-red-700 bg-red-50 border border-red-100';
            case 'warn':
            case 'warning': return 'text-amber-700 bg-amber-50 border border-amber-100';
            case 'success': return 'text-emerald-700 bg-emerald-50 border border-emerald-100';
            default: return 'text-blue-700 bg-blue-50 border border-blue-100';
        }
    }
};

const downloadLogs = () => {
    const content = props.logs.map(l => `[${formatTime(l.timestamp)}] [${l.level}] ${l.step ? '['+l.step+'] ' : ''}${l.message}`).join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-logs-${dayjs().format('YYYYMMDD-HHmmss')}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

watch(() => props.logs.length, () => {
    if (props.visible) scrollToBottom();
});

watch(() => props.visible, (val) => {
    if (val) scrollToBottom();
});

const scrollToBottom = () => {
    nextTick(() => {
        if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight;
        }
    });
};
</script>

<style scoped>
/* Tech Design Styles */
.tech-input {
    transition: all 0.3s ease;
    border-radius: 6px;
    background: #f1f5f9; /* slate-100 */
    border: 1px solid transparent;
}
.tech-input:hover {
    background: #e2e8f0; /* slate-200 */
}
.tech-input:focus-within {
    background: #ffffff;
    border-color: #cbd5e1; /* slate-300 */
    box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.2);
}

/* Dark Mode Input Overrides */
.tech-input.tech-input-dark {
    background: rgba(2, 6, 23, 0.6); /* slate-950 alpha */
    border: 1px solid rgba(30, 41, 59, 0.6); /* slate-800 alpha */
    color: #e2e8f0;
}
.tech-input.tech-input-dark:hover {
    border-color: rgba(51, 65, 85, 0.8); /* slate-700 */
    background: rgba(2, 6, 23, 0.8);
}
.tech-input.tech-input-dark:focus-within {
    border-color: rgba(6, 182, 212, 0.5); /* cyan-500 */
    box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.15);
    background: rgba(2, 6, 23, 0.9);
}

:global(.tech-input-dark .ant-input) {
    background: transparent !important;
    color: #e2e8f0 !important;
}
:global(.tech-input-dark .ant-input::placeholder) {
    color: #475569 !important;
}

/* Tech Select Styles */
.tech-select {
    border-radius: 6px;
}
:global(.tech-select .ant-select-selector) {
    background: #f1f5f9 !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    transition: all 0.3s ease !important;
}
:global(.tech-select:hover .ant-select-selector) {
    background: #e2e8f0 !important;
}
:global(.tech-select.ant-select-focused .ant-select-selector) {
    background: #ffffff !important;
    border-color: #cbd5e1 !important;
    box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.2) !important;
}

/* Dark Mode Select Overrides */
:global(.tech-select-dark .ant-select-selector) {
    background: rgba(2, 6, 23, 0.6) !important;
    border: 1px solid rgba(30, 41, 59, 0.6) !important;
    color: #e2e8f0 !important;
}
:global(.tech-select-dark:hover .ant-select-selector) {
    border-color: rgba(51, 65, 85, 0.8) !important;
    background: rgba(2, 6, 23, 0.8) !important;
}
:global(.tech-select-dark.ant-select-focused .ant-select-selector) {
    border-color: rgba(6, 182, 212, 0.5) !important;
    box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.15) !important;
    background: rgba(2, 6, 23, 0.9) !important;
}
:global(.tech-select-dark .ant-select-arrow) {
    color: #64748b !important;
}
:global(.tech-select-dark.ant-select-open .ant-select-arrow) {
    color: #22d3ee !important; /* cyan-400 */
}

/* Dropdown Menu Styles */
:global(.ant-select-dropdown) {
    padding: 4px !important;
    border-radius: 8px !important;
}
:global(.ant-select-dropdown) {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
}
:global(.log-drawer-dark .ant-select-dropdown) {
    background-color: #0f172a !important; /* slate-900 */
    border: 1px solid #334155 !important; /* slate-700 */
}
:global(.log-drawer-dark .ant-select-item) {
    color: #cbd5e1 !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}
:global(.log-drawer-dark .ant-select-item-option-selected) {
    background-color: rgba(6, 182, 212, 0.15) !important;
    color: #22d3ee !important;
    font-weight: 500;
}
:global(.log-drawer-dark .ant-select-item-option-active) {
    background-color: rgba(30, 41, 59, 0.8) !important;
}

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { 
    background: v-bind('isDarkMode ? "#334155" : "#cbd5e1"'); 
    border-radius: 4px; 
}
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

/* Force Ant Drawer Styles */
:global(.log-drawer-dark .ant-drawer-title) { color: #f8fafc !important; }
:global(.log-drawer-dark .ant-drawer-close) { color: #94a3b8 !important; }
:global(.log-drawer-dark .ant-drawer-close:hover) { color: #f8fafc !important; }

:global(.log-drawer-light .ant-drawer-title) { color: #0f172a !important; }
:global(.log-drawer-light .ant-drawer-close) { color: #64748b !important; }
:global(.log-drawer-light .ant-drawer-close:hover) { color: #0f172a !important; }
</style>
