<template>
  <div class="fixed inset-y-0 right-0 w-[400px] bg-background border-l shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col pointer-events-auto"
       :class="isOpen ? 'translate-x-0' : 'translate-x-full'">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b">
      <div class="flex items-center gap-2">
        <Bookmark class="w-4 h-4 text-amber-500" />
        <h3 class="font-semibold text-sm">秒记列表</h3>
        <Badge variant="secondary" class="text-xs h-5 px-1.5">{{ memos.length }}</Badge>
      </div>
      <Button variant="ghost" size="icon" class="h-8 w-8" @click="$emit('close')">
        <X class="w-4 h-4" />
      </Button>
    </div>

    <!-- Content -->
    <div class="flex-1 flex flex-col min-h-0">
        <div v-if="memos.length === 0" class="flex-1 flex flex-col items-center justify-center text-muted-foreground p-4">
          <Bookmark class="w-12 h-12 mb-3 opacity-20" />
          <p class="text-sm">暂无摘录内容</p>
          <p class="text-xs opacity-70 mt-1">点击消息上的书签图标进行摘录</p>
        </div>
        
        <ScrollArea v-else class="flex-1">
             <div class="p-4 space-y-4">
                <TransitionGroup name="list" tag="div" class="space-y-4">
          <Card v-for="(memo, index) in memos" :key="memo.id" class="relative group overflow-hidden border-l-4 border-l-amber-500 bg-card/50 hover:bg-card transition-colors">
            <CardHeader class="p-3 pb-2 space-y-0">
              <div class="flex justify-between items-start gap-2">
                <div class="flex items-center gap-2 text-xs text-muted-foreground">
                  <Avatar class="w-5 h-5">
                    <AvatarImage v-if="memo.avatar" :src="memo.avatar" />
                    <AvatarFallback>{{ memo.sender[0] }}</AvatarFallback>
                  </Avatar>
                  <span class="font-medium text-foreground/80">{{ memo.sender }}</span>
                  <span class="opacity-70">{{ formatTime(memo.timestamp) }}</span>
                </div>
                <div class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity -mr-2 -mt-2">
                    <Button v-if="editingId !== memo.id" variant="ghost" size="icon" class="h-6 w-6" 
                            @click="startEditing(memo)">
                      <Edit2 class="w-3.5 h-3.5 text-muted-foreground hover:text-primary" />
                    </Button>
                    <Button v-if="editingId !== memo.id" variant="ghost" size="icon" class="h-6 w-6" 
                            @click="removeMemo(memo.id)">
                      <Trash2 class="w-3.5 h-3.5 text-muted-foreground hover:text-destructive" />
                    </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent class="p-3 pt-0">
              <div v-if="editingId === memo.id" class="space-y-2">
                  <Textarea 
                    v-model="editContent" 
                    class="min-h-[100px] text-xs resize-none p-2"
                    autofocus
                  />
                  <div class="flex justify-end gap-2">
                      <Button size="sm" variant="ghost" class="h-6 px-2 text-xs" @click="cancelEditing">取消</Button>
                      <Button size="sm" class="h-6 px-2 text-xs" @click="saveEditing(memo.id)">保存</Button>
                  </div>
              </div>
              <div v-else class="text-sm leading-relaxed whitespace-pre-wrap line-clamp-[10] hover:line-clamp-none transition-all duration-200 cursor-text select-text"
                   @dblclick="startEditing(memo)">
                {{ memo.content }}
              </div>
            </CardContent>
          </Card>
        </TransitionGroup>
      </div>
    </ScrollArea>
    </div>
  </div>
  
  <!-- Overlay removed to allow interaction with chat while drawer is open -->
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { X, Bookmark, Trash2, Edit2 } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import dayjs from 'dayjs';

export interface Memo {
  id: string;
  content: string;
  sender: string;
  avatar?: string;
  timestamp: string;
}

defineProps<{
  isOpen: boolean;
  memos: Memo[];
}>();

const emit = defineEmits(['close', 'remove', 'update']);

const editingId = ref<string | null>(null);
const editContent = ref('');

const formatTime = (ts: string) => dayjs(ts).format('YYYY-MM-DD HH:mm');

const removeMemo = (id: string) => {
  emit('remove', id);
};

const startEditing = (memo: Memo) => {
  editingId.value = memo.id;
  editContent.value = memo.content;
  // Focus logic usually requires nextTick
  nextTick(() => {
    // If Textarea component exposes ref or inner element, we can focus
    // Assuming simple usage or direct element access if possible
    // Using autofocus on Textarea component often works
  });
};

const saveEditing = (id: string) => {
  if (editContent.value.trim()) {
    emit('update', id, editContent.value);
  }
  editingId.value = null;
};

const cancelEditing = () => {
  editingId.value = null;
};
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
