<script setup lang="ts">
import { ref, computed } from 'vue';

// --- 1. 类型定义 ---
type BlockType = 'text' | 'thought' | 'action' | 'artifact';
type ActionStatus = 'pending' | 'applied' | 'rejected';

interface MessageBlock {
  id: string;
  type: BlockType;
  content: string;
  path?: string;
  language?: string;
  status?: ActionStatus;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  blocks: MessageBlock[];
}

// --- 2. 模拟数据 ---
const messages = ref<Message[]>([
  {
    id: '1',
    role: 'user',
    blocks: [{ id: 'b1', type: 'text', content: '帮我修改一下登录按钮的样式，并展示一个预览界面。' }]
  },
  {
    id: '2',
    role: 'assistant',
    blocks: [
      {
        id: 'b2',
        type: 'thought',
        content: '用户需要修改登录按钮。我需要：1. 修改组件代码。2. 开启一个实时预览。'
      },
      {
        id: 'b3',
        type: 'text',
        content: '好的，我已经为你更新了 `LoginButton.vue`。我增加了更现代的渐变色和阴影效果。'
      },
      {
        id: 'b4',
        type: 'action',
        path: 'src/components/LoginButton.vue',
        content: '- <button class="bg-blue-500 text-white">Login</button>\n+ <button class="bg-gradient-to-r from-indigo-600 to-blue-500 hover:scale-105 transition-all text-white shadow-lg rounded-full px-6 py-2 font-medium">Login</button>',
        status: 'pending'
      },
      {
        id: 'b5',
        type: 'artifact',
        content: '<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f0f2f5;font-family:sans-serif;"><button style="background:linear-gradient(to right, #4f46e5, #3b82f6); border:none; padding:12px 24px; color:white; border-radius:30px; font-weight:500; cursor:pointer; box-shadow:0 10px 15px -3px rgba(59,130,246,0.5); transform:scale(1.1);">Login Now</button></body></html>',
        path: 'Preview: Login Button'
      }
    ]
  }
]);

// --- 3. 交互逻辑 ---
const activeArtifact = ref<MessageBlock | null>(null);

const handleApply = (blockId: string) => {
  messages.value.forEach(msg => {
    const block = msg.blocks.find(b => b.id === blockId);
    if (block) block.status = 'applied';
  });
};

const handleDiscard = (blockId: string) => {
  messages.value.forEach(msg => {
    const block = msg.blocks.find(b => b.id === blockId);
    if (block) block.status = 'rejected';
  });
};

const openArtifact = (block: MessageBlock) => {
  activeArtifact.value = block;
};
</script>

<template>
  <div class="flex h-screen w-full bg-[#f4f4f7] dark:bg-[#0a0a0a] text-zinc-900 dark:text-zinc-100 overflow-hidden font-sans">
    
    <!-- 左侧：对话区域 -->
    <div :class="['flex flex-col border-r border-zinc-200 dark:border-zinc-800 transition-all duration-500', activeArtifact ? 'w-1/2' : 'w-full max-w-4xl mx-auto']">
      <!-- 头部 -->
      <header class="h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-6 bg-white/50 dark:bg-black/50 backdrop-blur-md">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 bg-zinc-900 dark:bg-zinc-100 rounded-md flex items-center justify-center text-[10px] text-white dark:text-black font-bold">T</div>
          <span class="font-semibold text-sm tracking-tight">Trae Agent</span>
        </div>
        <button v-if="activeArtifact" @click="activeArtifact = null" class="text-xs text-zinc-500 hover:text-zinc-800 uppercase font-bold tracking-tighter">Close Preview</button>
      </header>

      <!-- 消息列表 -->
      <div class="flex-1 overflow-y-auto p-6 space-y-8">
        <div v-for="msg in messages" :key="msg.id" :class="['flex flex-col gap-4', msg.role === 'user' ? 'items-end' : 'items-start']">
          
          <div v-for="block in msg.blocks" :key="block.id" class="w-full max-w-[90%]">
            
            <!-- 1. TEXT BLOCK -->
            <div v-if="block.type === 'text'" :class="['p-3 rounded-2xl text-sm leading-relaxed', msg.role === 'user' ? 'bg-zinc-900 text-white ml-auto w-fit' : 'text-zinc-800 dark:text-zinc-200']">
              {{ block.content }}
            </div>

            <!-- 2. THOUGHT BLOCK (Claude 风格) -->
            <details v-else-if="block.type === 'thought'" class="group mb-4" open>
              <summary class="list-none cursor-pointer flex items-center gap-2 text-zinc-400 hover:text-zinc-500 transition-colors">
                <div class="w-4 h-4 rounded-full border border-zinc-300 dark:border-zinc-700 flex items-center justify-center group-open:rotate-180 transition-transform">
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="m6 9 6 6 6-6"/></svg>
                </div>
                <span class="text-[10px] font-bold uppercase tracking-widest">Thought</span>
              </summary>
              <div class="mt-2 pl-6 border-l-2 border-zinc-100 dark:border-zinc-800 text-xs text-zinc-500 italic">
                {{ block.content }}
              </div>
            </details>

            <!-- 3. ACTION BLOCK (Trae 风格) -->
            <div v-else-if="block.type === 'action'" class="my-4 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
              <div class="px-4 py-2 bg-zinc-50 dark:bg-zinc-800/50 flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800">
                <div class="flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                  <span class="text-xs font-mono font-medium truncate max-w-[200px]">{{ block.path }}</span>
                </div>
                <div class="flex gap-2">
                  <template v-if="block.status === 'pending'">
                    <button @click="handleDiscard(block.id)" class="px-2 py-1 text-[10px] font-bold text-zinc-500 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded">DISCARD</button>
                    <button @click="handleApply(block.id)" class="px-2 py-1 text-[10px] font-bold bg-blue-600 text-white rounded hover:bg-blue-700">APPLY</button>
                  </template>
                  <span v-else :class="['text-[10px] font-bold px-2 py-1 rounded', block.status === 'applied' ? 'bg-green-100 text-green-700' : 'bg-zinc-100 text-zinc-500']">
                    {{ block.status?.toUpperCase() }}
                  </span>
                </div>
              </div>
              <div class="p-4 bg-[#0d0d0d] text-[12px] font-mono leading-6 overflow-x-auto text-zinc-300">
                <div v-for="line in block.content.split('\n')" :class="line.startsWith('+') ? 'text-green-400 bg-green-900/20' : line.startsWith('-') ? 'text-red-400 bg-red-900/20' : ''">
                  {{ line }}
                </div>
              </div>
            </div>

            <!-- 4. ARTIFACT BLOCK (Claude 风格) -->
            <button v-else-if="block.type === 'artifact'" @click="openArtifact(block)" 
              class="w-full my-2 flex items-center gap-4 p-4 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900 hover:border-blue-500 transition-all text-left group">
              <div class="w-10 h-10 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
              </div>
              <div class="flex-1">
                <div class="text-xs font-bold uppercase text-zinc-400 tracking-tighter">Preview Artifact</div>
                <div class="text-sm font-medium">{{ block.path }}</div>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-zinc-300"><path d="m9 18 6-6-6-6"/></svg>
            </button>

          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <footer class="p-6">
        <div class="max-w-3xl mx-auto relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-xl p-2">
          <textarea placeholder="Ask Agent to do something..." class="w-full bg-transparent border-none focus:ring-0 text-sm p-3 h-12 resize-none" readonly></textarea>
          <div class="flex justify-between items-center px-2 pt-1 border-t border-zinc-50 dark:border-zinc-800">
            <div class="flex gap-2">
              <div class="w-5 h-5 rounded bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] text-zinc-500 font-bold">/</div>
            </div>
            <button class="bg-zinc-900 dark:bg-zinc-100 text-white dark:text-black p-1.5 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>
            </button>
          </div>
        </div>
      </footer>
    </div>

    <!-- 右侧：Artifact 预览窗口 (Claude 核心体验) -->
    <transition name="slide">
      <div v-if="activeArtifact" class="w-1/2 bg-white dark:bg-[#0a0a0a] flex flex-col shadow-2xl z-10">
        <div class="h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-6">
          <span class="text-xs font-bold uppercase tracking-widest text-zinc-500">Live Preview</span>
          <div class="flex gap-4">
            <button class="text-xs text-blue-600 font-bold tracking-tighter">Code</button>
            <button class="text-xs text-zinc-400 font-bold tracking-tighter">Preview</button>
          </div>
        </div>
        <div class="flex-1 bg-zinc-50 dark:bg-zinc-950 p-8">
          <div class="w-full h-full bg-white dark:bg-black rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
             <!-- 模拟 Iframe 渲染内容 -->
             <iframe v-if="activeArtifact.content" class="w-full h-full border-none" :srcdoc="activeArtifact.content"></iframe>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<style>
/* 隐藏滚动条 */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-thumb {
  background: #e4e4e7;
  border-radius: 10px;
}

/* 动画效果 */
.slide-enter-active, .slide-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}

summary::-webkit-details-marker {
  display: none;
}
</style>