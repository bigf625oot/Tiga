<script setup lang="ts">
import { ref, computed } from 'vue';
import { usePipelineStore } from '../composables/usePipelineStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { History, Save, RotateCcw, Clock, Trash2, Check, X } from 'lucide-vue-next';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const store = usePipelineStore();
const isOpen = ref(false);
const newVersionName = ref('');
const isCreating = ref(false);

const versions = computed(() => store.versions);

const createVersion = () => {
  if (!newVersionName.value.trim()) return;
  store.createVersion(newVersionName.value);
  newVersionName.value = '';
  isCreating.value = false;
};

const restoreVersion = (id: string) => {
  if (confirm('恢复版本将覆盖当前画布内容，确定继续吗？')) {
    store.restoreVersion(id);
    isOpen.value = false;
  }
};

const formatDate = (timestamp: number) => {
  return dayjs(timestamp).fromNow();
};
</script>

<template>
  <Sheet v-model:open="isOpen">
    <SheetTrigger as-child>
      <Button variant="outline" size="sm" class="gap-2 h-8">
        <History class="w-4 h-4" />
        <span class="hidden sm:inline">版本历史</span>
      </Button>
    </SheetTrigger>
    <SheetContent class="w-[400px] sm:w-[540px] flex flex-col h-full">
      <SheetHeader>
        <SheetTitle class="flex items-center gap-2">
          <History class="w-5 h-5" />
          版本控制
        </SheetTitle>
        <SheetDescription>
          创建快照以保存当前工作状态，或恢复到之前的版本。
        </SheetDescription>
      </SheetHeader>

      <div class="py-6 flex-1 flex flex-col min-h-0 gap-4">
        <!-- Create New Version -->
        <div class="p-4 border rounded-lg bg-muted/20 space-y-3">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-medium">当前状态</h4>
            <Button 
              v-if="!isCreating" 
              size="sm" 
              variant="secondary" 
              class="h-7 text-xs" 
              @click="isCreating = true"
            >
              <Save class="w-3.5 h-3.5 mr-1.5" />
              创建新版本
            </Button>
          </div>
          
          <div v-if="isCreating" class="space-y-3 pt-2 animate-in fade-in slide-in-from-top-2">
            <div class="space-y-1">
              <label class="text-xs text-muted-foreground">版本名称</label>
              <Input 
                v-model="newVersionName" 
                placeholder="e.g. 完成数据清洗配置" 
                class="h-8 text-sm" 
                @keyup.enter="createVersion"
                autoFocus
              />
            </div>
            <div class="flex justify-end gap-2">
              <Button variant="ghost" size="sm" class="h-7 text-xs" @click="isCreating = false">取消</Button>
              <Button size="sm" class="h-7 text-xs" @click="createVersion" :disabled="!newVersionName.trim()">保存</Button>
            </div>
          </div>
        </div>

        <!-- History List -->
        <div class="flex-1 flex flex-col min-h-0">
          <h4 class="text-sm font-medium mb-3 flex items-center gap-2">
            <Clock class="w-4 h-4 text-muted-foreground" />
            历史记录 ({{ versions.length }})
          </h4>
          
          <ScrollArea class="flex-1 pr-4 -mr-4">
            <div v-if="versions.length === 0" class="flex flex-col items-center justify-center h-[200px] text-muted-foreground text-sm border border-dashed rounded-lg">
              <History class="w-8 h-8 mb-2 opacity-20" />
              <p>暂无版本记录</p>
              <p class="text-xs opacity-60">点击上方按钮创建第一个版本</p>
            </div>
            
            <div v-else class="space-y-3">
              <div 
                v-for="version in versions" 
                :key="version.id" 
                class="group flex flex-col p-3 rounded-lg border bg-card hover:shadow-md transition-all relative overflow-hidden"
              >
                <div class="flex justify-between items-start mb-2">
                  <div class="space-y-1">
                    <div class="font-medium text-sm flex items-center gap-2">
                      {{ version.name }}
                    </div>
                    <div class="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock class="w-3 h-3" />
                      {{ formatDate(version.timestamp) }}
                    </div>
                  </div>
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    class="h-7 text-xs opacity-0 group-hover:opacity-100 transition-opacity gap-1.5"
                    @click="restoreVersion(version.id)"
                  >
                    <RotateCcw class="w-3.5 h-3.5" />
                    恢复
                  </Button>
                </div>
                
                <div class="text-[10px] text-muted-foreground bg-muted/30 p-1.5 rounded flex gap-4">
                  <span>节点: {{ version.data.nodes.length }}</span>
                  <span>连线: {{ version.data.edges.length }}</span>
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>
    </SheetContent>
  </Sheet>
</template>
