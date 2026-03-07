<template>
  <div class="flex h-full w-full transition-colors duration-300 bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-gray-100">
    
    <!-- Left Sidebar -->
    <div class="w-64 flex flex-col border-r dark:border-none transition-colors bg-white dark:bg-slate-900/80 dark:backdrop-blur-xl border-border dark:shadow-[1px_0_0_0_rgba(255,255,255,0.05)]">
      <!-- Sidebar Header -->
      <div class="h-16 flex items-center px-6 border-b transition-colors border-border dark:border-none dark:shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
        <div class="flex items-center gap-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white shadow-lg shadow-primary/30">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div>
            <h1 class="font-semibold text-sm leading-tight">系统设置</h1>
            <p class="text-[10px] opacity-60">System Settings</p>
          </div>
        </div>
      </div>

      <!-- Menu Items -->
      <div class="flex-1 py-6 p-4 space-y-2">
        <div 
          v-for="item in menuItems" 
          :key="item.id"
          @click="activeTab = item.id"
          class="flex items-center gap-4 px-4 p-4 rounded-lg cursor-pointer transition-all duration-200 group relative overflow-hidden"
          :class="activeTab === item.id 
            ? 'bg-primary/10 text-primary border border-blue-100 shadow-sm dark:bg-white/5 dark:text-[#00D1FF] dark:border-none dark:shadow-[0_0_15px_rgba(0,209,255,0.15)]' 
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5'"
        >
          <!-- Active Indicator Line (Left) -->
          <div v-if="activeTab === item.id" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-blue-500 dark:bg-[#00D1FF] dark:shadow-[0_0_8px_#00D1FF]"></div>

          <component :is="item.icon" class="w-5 h-5 flex-shrink-0" :class="activeTab === item.id ? 'text-blue-500 dark:text-[#00D1FF]' : 'opacity-70 group-hover:opacity-100'" />
          
          <div class="flex flex-col">
            <span class="text-sm font-medium">{{ item.label }}</span>
            <span class="text-[10px] opacity-50">{{ item.subLabel }}</span>
          </div>

          <svg v-if="activeTab === item.id" class="w-4 h-4 ml-auto text-blue-500 dark:text-[#00D1FF] opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>

      <!-- Bottom User Profile -->
      <!-- Theme Toggle Removed -->
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-full overflow-hidden relative">
      <!-- Top Bar -->
      <div class="h-16 px-8 flex items-center justify-between shrink-0 transition-colors bg-white/50 dark:bg-slate-900/50 backdrop-blur border-b border-border dark:border-none dark:shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
        <div class="flex items-center gap-4">
          <h2 class="text-lg font-semibold dark:text-gray-100">模型配置</h2>
          <span class="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider bg-[#1E3A8A] text-[#60A5FA] border border-[#1E40AF]">ADMIN</span>
        </div>
        
        <div class="flex items-center gap-4">
          <button class="flex items-center gap-1.5 text-xs font-medium transition-colors hover:text-blue-500 text-gray-500 dark:text-gray-400 dark:hover:text-blue-400">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            重置配置
          </button>
          <button class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors text-gray-400">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content Scroll -->
      <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div class="max-w-5xl mx-auto space-y-6">
          
          <div v-if="activeTab === 'model'" class="space-y-6">
          <!-- Embedding Model Card -->
          <div class="rounded-lg border p-6 transition-all duration-300 bg-white border-border shadow-sm">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="text-lg font-semibold flex items-center gap-2">
                  Embedding Model
                  <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                </h3>
                <p class="text-xs mt-1 opacity-60">向量化模型配置</p>
              </div>
              <div class="p-4 py-1 rounded-full text-xs font-medium bg-[#064E3B] text-[#34D399] border border-[#065F46] flex items-center gap-1.5">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                已连接
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <!-- Select Model -->
              <div class="space-y-2">
                <label class="text-xs font-medium opacity-70 ml-1">选择模型</label>
                <div class="relative">
                  <select class="w-full h-11 pl-4 pr-10 rounded-lg appearance-none outline-none transition-all border font-medium text-sm bg-gray-50 border-border text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
                    <option>text-embedding-3-large (3072d)</option>
                    <option>text-embedding-3-small (1536d)</option>
                    <option>text-embedding-ada-002 (1536d)</option>
                  </select>
                  <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-50">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </div>
              </div>

              <!-- API Key -->
              <div class="space-y-2">
                <label class="text-xs font-medium opacity-70 ml-1">API Key</label>
                <div class="relative">
                  <input type="password" value="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" readonly 
                    class="w-full h-11 pl-4 pr-10 rounded-lg outline-none transition-all border font-mono text-sm tracking-widest bg-gray-50 border-border text-gray-900"
                  >
                  <div class="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer opacity-50 hover:opacity-100">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-4">
              <div class="p-4 rounded-lg border relative overflow-hidden group bg-gray-50 border-gray-100">
                <div class="relative z-10">
                  <div class="text-[10px] font-medium opacity-50 mb-1">向量维度</div>
                  <div class="text-xl font-semibold font-din">3072</div>
                </div>
                <div class="absolute right-2 bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
                  <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                </div>
              </div>

              <div class="p-4 rounded-lg border relative overflow-hidden group bg-gray-50 border-gray-100">
                <div class="relative z-10">
                  <div class="text-[10px] font-medium text-blue-400 mb-1">本月消耗</div>
                  <div class="text-xl font-semibold text-blue-500 font-din">1.04M <span class="text-xs font-normal opacity-70">tokens</span></div>
                </div>
                <div class="absolute right-0 bottom-0 opacity-10 group-hover:opacity-20 transition-opacity">
                  <svg class="w-16 h-16 text-blue-500 translate-x-4 translate-y-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                </div>
              </div>

              <div class="p-4 rounded-lg border relative overflow-hidden group bg-gray-50 border-gray-100">
                <div class="relative z-10">
                  <div class="text-[10px] font-medium text-green-400 mb-1">预估费用</div>
                  <div class="text-xl font-semibold text-green-500 font-din">$13.52</div>
                </div>
                <div class="absolute right-2 bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
                  <svg class="w-12 h-12 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
              </div>
            </div>
          </div>

          <!-- RAG LLM Card -->
          <div class="rounded-lg border p-6 transition-all duration-300 bg-white border-border shadow-sm">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="text-lg font-semibold flex items-center gap-2">
                  RAG LLM
                  <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                </h3>
                <p class="text-xs mt-1 opacity-60">大语言模型配置</p>
              </div>
              <div class="p-4 py-1 rounded-full text-xs font-medium bg-[#064E3B] text-[#34D399] border border-[#065F46] flex items-center gap-1.5">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                已连接
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <!-- Select Model -->
              <div class="space-y-2">
                <label class="text-xs font-medium opacity-70 ml-1">选择模型</label>
                <div class="relative">
                  <select class="w-full h-11 pl-4 pr-10 rounded-lg appearance-none outline-none transition-all border font-medium text-sm bg-gray-50 border-border text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-100">
                    <option>GPT-4 Turbo (128K context)</option>
                    <option>GPT-4o</option>
                    <option>Claude 3.5 Sonnet</option>
                  </select>
                  <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-50">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </div>
              </div>

              <!-- Temperature Slider -->
              <div class="space-y-4 pt-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium opacity-70">Temperature</label>
                  <span class="text-xs font-mono opacity-80 bg-gray-800 px-1.5 py-0.5 rounded text-gray-300">{{ temperature }}</span>
                </div>
                <div class="relative h-2 rounded-full w-full bg-gray-700">
                   <input 
                    type="range" 
                    v-model="temperature" 
                    min="0" 
                    max="1" 
                    step="0.1"
                    class="absolute w-full h-full opacity-0 cursor-pointer z-10"
                   />
                   <div class="absolute top-0 left-0 h-full bg-blue-500 rounded-full" :style="{ width: (temperature * 100) + '%' }"></div>
                   <div class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-[#13151A] shadow-lg pointer-events-none transition-all" :style="{ left: (temperature * 100) + '%' }"></div>
                </div>
                <div class="flex justify-between text-[10px] opacity-40">
                  <span>Precise</span>
                  <span>Balanced</span>
                  <span>Creative</span>
                </div>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-4">
              <div class="p-4 rounded-lg border relative overflow-hidden group bg-gray-50 border-gray-100">
                <div class="relative z-10">
                  <div class="text-[10px] font-medium opacity-50 mb-1">上下文长度</div>
                  <div class="text-xl font-semibold font-din">128K</div>
                </div>
                <div class="absolute right-2 bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
                  <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
                </div>
              </div>

              <div class="p-4 rounded-lg border relative overflow-hidden group bg-gray-50 border-gray-100">
                <div class="relative z-10">
                  <div class="text-[10px] font-medium text-purple-400 mb-1">本月消耗</div>
                  <div class="text-xl font-semibold text-purple-500 font-din">3.69M <span class="text-xs font-normal opacity-70">tokens</span></div>
                </div>
                <div class="absolute right-0 bottom-0 opacity-10 group-hover:opacity-20 transition-opacity">
                   <svg class="w-16 h-16 text-purple-500 translate-x-4 translate-y-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                </div>
              </div>

              <div class="p-4 rounded-lg border relative overflow-hidden group bg-gray-50 border-gray-100">
                <div class="relative z-10">
                  <div class="text-[10px] font-medium text-green-400 mb-1">预估费用</div>
                  <div class="text-xl font-semibold text-green-500 font-din">$110.70</div>
                </div>
                <div class="absolute right-2 bottom-2 opacity-10 group-hover:opacity-20 transition-opacity">
                  <svg class="w-12 h-12 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
              </div>
            </div>
          </div>
          </div>

          <DatabaseConnectionConfig v-if="activeTab === 'database'" />
          <AlertRulesConfig v-if="activeTab === 'alert'" />

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue';
import DatabaseConnectionConfig from './components/DatabaseConnectionConfig.vue';
import AlertRulesConfig from './components/AlertRulesConfig.vue';

const activeTab = ref('model');
const temperature = ref(0.7);

const menuItems = [
  { 
    id: 'model', 
    label: '模型配置', 
    subLabel: 'LLM & Embedding 配置',
    icon: h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" })])
  },
  { 
    id: 'database', 
    label: '数据库连接', 
    subLabel: 'Neo4j & 向量库',
    icon: h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" })])
  },
  { 
    id: 'alert', 
    label: '告警规则', 
    subLabel: '系统监控告警',
    icon: h('svg', { xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [h('path', { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" })])
  },
];
</script>

<style scoped>
/* Custom Range Input Styling */
input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  height: 0;
  width: 0;
}
</style>