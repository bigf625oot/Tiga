<script setup lang="ts">
import { Box, Search, ArrowLeft, X, Play, Save, Square, Edit2 } from 'lucide-vue-next';
import PipelineCanvas from './components/PipelineCanvas.vue';
import Sidebar from './components/Sidebar.vue';
import PropertyPanel from './components/PropertyPanel.vue';
import VersionHistory from './components/VersionHistory.vue';
import RunLogs from './components/RunLogs.vue';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { usePipelineStore } from './composables/usePipelineStore';
import { ref, watch, computed, nextTick } from 'vue';

const emit = defineEmits(['back']);
const searchQuery = ref('');
const store = usePipelineStore();

// Property Panel Resize Logic
const panelWidth = ref(450);
const isResizing = ref(false);

const startResize = (e: MouseEvent) => {
  isResizing.value = true;
  const startX = e.clientX;
  const startWidth = panelWidth.value;

  const onMouseMove = (e: MouseEvent) => {
    if (!isResizing.value) return;
    const delta = startX - e.clientX;
    const newWidth = Math.max(300, Math.min(800, startWidth + delta));
    panelWidth.value = newWidth;
  };

  const onMouseUp = () => {
    isResizing.value = false;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  };

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
  document.body.style.cursor = 'ew-resize';
  document.body.style.userSelect = 'none'; // Prevent text selection during resize
};

const isEditingName = ref(false);
const editingName = ref('');
const nameInputRef = ref<InstanceType<typeof Input> | null>(null);

const startEditingName = async () => {
  if (!store.currentPipeline) return;
  editingName.value = store.currentPipeline.name;
  isEditingName.value = true;
  await nextTick();
  // Try to focus the input - note that Input component might need to expose focus
  // Or we can use a directive or template ref on the native input if Input forwards attrs
  const inputEl = document.querySelector('input[name="pipeline-name"]');
  if (inputEl instanceof HTMLInputElement) {
    inputEl.focus();
  }
};

const saveName = async () => {
  if (!store.currentPipeline || !editingName.value.trim()) {
      isEditingName.value = false;
      return;
  }
  if (editingName.value.trim() !== store.currentPipeline.name) {
    store.currentPipeline.name = editingName.value.trim();
    await store.savePipeline();
  }
  isEditingName.value = false;
};

// Control drawer open state based on selected node
const isPropertyPanelOpen = computed({
  get: () => !!store.selectedNodeId,
  set: (val) => {
    if (!val) store.setSelectedNode(null);
  }
});
</script>

<template>
  <div class="flex h-screen w-full bg-background overflow-hidden">
    <!-- Left Sidebar - Component Library -->
    <div class="w-64 bg-card border-r border-border flex flex-col z-10 shadow-sm">
      <div class="p-4 border-b border-border space-y-4">
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="icon" class="h-8 w-8" @click="emit('back')">
            <ArrowLeft class="w-4 h-4" />
          </Button>
          <div class="p-1.5 bg-primary/10 rounded-md">
            <Box class="w-5 h-5 text-primary" />
          </div>
          <h1 class="font-semibold text-foreground tracking-tight">ETL Studio</h1>
        </div>
        <div class="relative">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            v-model="searchQuery"
            placeholder="搜索组件..." 
            class="pl-9 h-9 bg-background/50"
          />
        </div>
      </div>
      
      <Sidebar :search-query="searchQuery" />
    </div>

    <!-- Main Canvas Area -->
    <div class="flex-1 relative flex flex-col min-w-0">
      <!-- Top Toolbar -->
      <div class="h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-4 shrink-0 z-20">
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-2 group">
            <template v-if="isEditingName">
              <Input 
                name="pipeline-name"
                v-model="editingName" 
                class="h-7 w-64 text-sm font-medium" 
                @blur="saveName"
                @keyup.enter="saveName"
              />
            </template>
            <template v-else>
              <div class="font-medium text-sm cursor-pointer hover:underline underline-offset-4 decoration-muted-foreground/30" @click="startEditingName">
                {{ store.currentPipeline?.name || '未命名流水线' }}
              </div>
              <Button variant="ghost" size="icon" class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity" @click="startEditingName">
                <Edit2 class="w-3 h-3 text-muted-foreground" />
              </Button>
            </template>
          </div>
          <span class="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full" v-if="store.currentPipeline?.status">
            {{ store.currentPipeline.status }}
          </span>
        </div>
        
        <div class="flex items-center gap-2">
          <RunLogs />
          <VersionHistory />
          
          <Button variant="outline" size="sm" class="gap-2 h-8" @click="store.savePipeline" :disabled="store.loading">
            <Save class="w-4 h-4" />
            <span class="hidden sm:inline">保存</span>
          </Button>
          
          <Button 
            size="sm" 
            class="gap-2 h-8" 
            :variant="store.isRunning ? 'destructive' : 'default'"
            @click="store.isRunning ? store.stopPipeline() : store.runPipeline()" 
            :disabled="store.loading"
          >
            <template v-if="store.isRunning">
              <Square class="w-4 h-4 fill-current" />
              <span class="hidden sm:inline">停止</span>
            </template>
            <template v-else>
              <Play class="w-4 h-4 fill-current" />
              <span class="hidden sm:inline">运行</span>
            </template>
          </Button>
        </div>
      </div>

      <!-- Canvas -->
      <div class="flex-1 relative">
        <PipelineCanvas />
      </div>
    </div>

    <!-- Right Drawer - Properties (Custom Resizable Panel) -->
    <Transition name="slide">
      <div 
        v-if="isPropertyPanelOpen" 
        class="fixed right-0 top-0 h-full bg-background border-l shadow-xl z-50 flex flex-col"
        :style="{ width: panelWidth + 'px' }"
      >
        <!-- Resize Handle -->
        <div 
          class="absolute left-0 top-0 bottom-0 w-1.5 -ml-0.5 cursor-ew-resize hover:bg-primary/50 transition-colors z-[60]"
          @mousedown="startResize"
        ></div>
        
        <!-- Close Button -->
        <Button 
          variant="ghost" 
          size="icon" 
          class="absolute right-4 top-4 z-[60] h-8 w-8 text-muted-foreground hover:text-foreground"
          @click="store.setSelectedNode(null)"
        >
          <X class="w-4 h-4" />
        </Button>

        <PropertyPanel />
      </div>
    </Transition>
  </div>
</template>

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
