<template>
  <div class="flex h-screen w-full bg-background overflow-hidden">
    <!-- Left Sidebar -->
    <div 
      class="border-r border-border flex flex-col bg-background/95 backdrop-blur transition-all duration-300 ease-in-out w-64"
    >
      <div class="p-4 border-b border-border space-y-4 shrink-0">
        <div class="relative">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="搜索节点..." 
            class="pl-9 h-9 bg-muted/50"
          />
        </div>
      </div>
      
      <AgentFlowSidebar />
    </div>

    <!-- Main Canvas Area -->
    <div class="flex-1 relative flex flex-col min-w-0">
      <!-- Top Toolbar -->
      <div class="h-14 border-b bg-background/95 backdrop-blur flex items-center justify-between px-4 shrink-0 z-20">
        <div class="flex items-center gap-4">
          <Button variant="ghost" size="icon" class="h-8 w-8" @click="handleBack" title="返回智能体流">
            <ArrowLeft class="w-4 h-4" />
          </Button>
          <div class="h-4 w-px bg-border mx-1"></div>
          
          <div class="flex items-center gap-2 group min-w-[200px]">
            <div class="p-1.5 bg-primary/10 rounded-md mr-1">
              <GitBranch class="w-5 h-5 text-primary" />
            </div>
            
            <div class="flex items-center gap-2">
              <div v-if="isEditingName" class="flex-1">
                <Input 
                  id="agent-flow-name-input"
                  v-model="store.flowName" 
                  class="h-8 text-sm" 
                  autoFocus
                  @blur="isEditingName = false"
                  @keyup.enter="isEditingName = false"
                />
              </div>
              <div 
                v-else 
                class="flex items-center gap-2 cursor-pointer hover:bg-muted/50 px-2 py-0.5 rounded-md transition-colors"
                @click="startEditingName"
              >
                <div class="font-medium text-sm truncate max-w-[300px]" :title="store.flowName">
                  {{ store.flowName || '未命名智能体流' }}
                </div>
                <Edit2 class="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              
              <!-- Flow Version -->
              <div class="flex items-center gap-1 text-[10px] text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-full cursor-pointer hover:bg-muted transition-colors">
                <History class="w-3 h-3" />
                <span>v1.0.0</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <!-- Run Logs -->
          <Button variant="ghost" size="sm" class="gap-2 h-8 text-muted-foreground hover:text-foreground">
            <ScrollText class="w-4 h-4" />
            <span class="hidden sm:inline">运行日志</span>
          </Button>

          <div class="h-4 w-px bg-border mx-1"></div>

          <Button variant="outline" size="sm" class="gap-2 h-8" @click="store.saveFlow" :disabled="store.loading">
            <Save class="w-4 h-4" />
            <span class="hidden sm:inline">保存</span>
          </Button>
          
          <Button 
            size="sm" 
            class="gap-2 h-8" 
            :variant="store.isRunning ? 'destructive' : 'default'"
            @click="handleRunClick" 
            :disabled="store.loading"
          >
            <template v-if="store.isRunning">
              <Square class="w-4 h-4 fill-current" />
              <span class="hidden sm:inline">停止</span>
            </template>
            <template v-else>
              <Play class="w-4 h-4 fill-current" />
              <span class="hidden sm:inline">试运行</span>
            </template>
          </Button>
        </div>
      </div>

      <!-- Canvas -->
      <div class="flex-1 relative">
        <AgentFlowCanvas />
      </div>
    </div>

    <!-- Right Drawer - Properties -->
    <Transition name="slide">
      <div 
        v-if="store.selectedNodeId" 
        class="absolute right-0 top-0 h-full z-50 shadow-xl"
      >
        <AgentFlowPropertyPanel @close="store.setSelectedNode(null)" />
      </div>
    </Transition>

    <!-- Run Drawer (Chat Interface) -->
    <Sheet v-model:open="isRunDrawerOpen">
      <SheetContent class="w-[400px] sm:w-[540px] flex flex-col p-0 gap-0 sm:max-w-[540px]">
        <SheetHeader class="px-6 py-4 border-b shrink-0">
          <SheetTitle class="flex items-center gap-2">
            <Play class="w-4 h-4 text-primary" />
            试运行
          </SheetTitle>
          <SheetDescription>
            依据当前配置的流程进行对话测试。
          </SheetDescription>
        </SheetHeader>
        
        <!-- Chat Area -->
        <div class="flex-1 overflow-hidden flex flex-col relative bg-muted/5">
           <!-- Messages -->
           <ScrollArea class="flex-1 p-6" ref="messagesScrollArea">
             <div class="space-y-6">
               <div v-if="chatMessages.length === 0" class="flex flex-col items-center justify-center py-10 text-center text-muted-foreground opacity-50">
                 <Bot class="w-12 h-12 mb-4 stroke-1" />
                 <p class="text-sm">输入内容开始测试您的智能体流...</p>
               </div>
               
               <div v-for="(msg, index) in chatMessages" :key="index" 
                 class="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300" 
                 :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
               >
                 <!-- Avatar -->
                 <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border shadow-sm"
                   :class="msg.role === 'user' ? 'bg-primary text-primary-foreground border-primary' : 'bg-background border-border'"
                 >
                   <span v-if="msg.role === 'user'" class="text-xs font-bold">ME</span>
                   <Bot v-else class="w-4 h-4" />
                 </div>
                 
                 <!-- Content -->
                 <div class="flex flex-col gap-1 max-w-[85%]" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
                    <div class="px-4 py-3 text-sm shadow-sm"
                      :class="msg.role === 'user' ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm' : 'bg-background border border-border rounded-2xl rounded-tl-sm'"
                    >
                      <div class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</div>
                    </div>
                    <span class="text-[10px] text-muted-foreground px-1">{{ formatTime(msg.timestamp) }}</span>
                 </div>
               </div>
               
               <!-- Loading State -->
                <div v-if="store.isRunning" class="flex gap-4 animate-in fade-in duration-300">
                 <div class="w-8 h-8 rounded-full bg-background border border-border flex items-center justify-center shrink-0 shadow-sm">
                   <Bot class="w-4 h-4" />
                 </div>
                 <div class="bg-background border border-border rounded-2xl rounded-tl-sm p-4 flex items-center gap-1.5 shadow-sm">
                   <div class="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                   <div class="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                   <div class="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                 </div>
               </div>
             </div>
           </ScrollArea>
           
           <!-- Input Area -->
           <div class="p-4 border-t bg-background/80 backdrop-blur shrink-0">
             <div class="relative group">
               <Textarea 
                 v-model="chatInput" 
                 placeholder="输入消息..." 
                 class="min-h-[50px] max-h-[200px] resize-none pr-12 py-3 rounded-xl border-muted-foreground/20 focus:border-primary/50 transition-all bg-background"
                 @keydown.enter.prevent="handleSendMessage"
               />
               <Button 
                 size="icon" 
                 class="absolute right-2 bottom-2 h-8 w-8 transition-transform active:scale-95"
                 :class="chatInput.trim() ? 'opacity-100' : 'opacity-50'"
                 :disabled="!chatInput.trim() || store.isRunning"
                 @click="handleSendMessage"
               >
                 <Send class="w-4 h-4" />
               </Button>
             </div>
             <div class="flex justify-between items-center mt-2 px-1">
                <span class="text-[10px] text-muted-foreground">按 Enter 发送，Shift + Enter 换行</span>
                <Button variant="ghost" size="sm" class="h-6 text-[10px] text-muted-foreground hover:text-destructive gap-1" @click="clearHistory" v-if="chatMessages.length > 0">
                    <Trash2 class="w-3 h-3" />
                    清空历史
                </Button>
             </div>
           </div>
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';
import { Search, ArrowLeft, GitBranch, Edit2, Save, Play, Square, History, ScrollText, Bot, Send, Trash2 } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAgentFlowStore } from '../store/agentFlow.store';
import AgentFlowSidebar from './flow/AgentFlowSidebar.vue';
import AgentFlowCanvas from './flow/AgentFlowCanvas.vue';
import AgentFlowPropertyPanel from './flow/AgentFlowPropertyPanel.vue';
import dayjs from 'dayjs';

const emit = defineEmits(['back']);
const store = useAgentFlowStore();

const handleBack = () => {
  emit('back');
};

const isEditingName = ref(false);
const nameInput = ref<InstanceType<typeof Input> | null>(null);

const startEditingName = async () => {
  isEditingName.value = true;
  await nextTick();
  const inputEl = document.getElementById('agent-flow-name-input');
  if (inputEl) {
    inputEl.focus();
  }
};

// Run Drawer Logic
const isRunDrawerOpen = ref(false);
const chatInput = ref('');
const chatMessages = ref<Array<{role: 'user' | 'assistant', content: string, timestamp: number}>>([]);
const messagesScrollArea = ref<any>(null);

const handleRunClick = () => {
  isRunDrawerOpen.value = true;
};

const formatTime = (ts: number) => dayjs(ts).format('HH:mm');

const scrollToBottom = async () => {
  await nextTick();
  // Simple scroll logic, assuming ScrollArea renders a viewport
  const viewport = document.querySelector('[data-radix-scroll-area-viewport]');
  if (viewport) {
    viewport.scrollTop = viewport.scrollHeight;
  }
};

const handleSendMessage = async () => {
  const content = chatInput.value.trim();
  if (!content || store.isRunning) return;

  // Add user message
  chatMessages.value.push({
    role: 'user',
    content,
    timestamp: Date.now()
  });
  
  chatInput.value = '';
  await scrollToBottom();

  // Run flow
  store.isRunning = true; // Manually set for UI feedback
  try {
    // Simulate run with delay
    // In real implementation, this would call store.runFlow(content) and await response
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Simulate response
    chatMessages.value.push({
      role: 'assistant',
      content: `模拟回复：收到了您的输入 "${content}"。\n流程执行成功。`,
      timestamp: Date.now()
    });
  } catch (error) {
    chatMessages.value.push({
      role: 'assistant',
      content: `执行出错: ${error}`,
      timestamp: Date.now()
    });
  } finally {
    store.isRunning = false;
    await scrollToBottom();
  }
};

const clearHistory = () => {
  chatMessages.value = [];
};

watch(isRunDrawerOpen, (open) => {
  if (open) {
    scrollToBottom();
  }
});
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
