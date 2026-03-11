<template>
  <div class="flex flex-col h-full bg-background border-r">
    <div class="p-4 border-b space-y-4">
      <div class="flex items-center gap-2 font-semibold text-sm text-foreground">
        <ScanIcon class="h-4 w-4" />
        <span>关系修复检测</span>
      </div>
      <div class="space-y-3">
        <div class="space-y-1.5">
          <Label class="text-xs text-muted-foreground">主节点</Label>
          <Input v-model="localMainNode" placeholder="例如: 中国联通" class="h-8 text-sm" />
        </div>
        <div class="space-y-1.5">
          <Label class="text-xs text-muted-foreground">包含关键词</Label>
          <Input v-model="localKeyword" placeholder="例如: 联通" class="h-8 text-sm" />
        </div>
        <Button 
          @click="handleDetect" 
          class="w-full h-8 text-xs"
          :disabled="loading"
        >
          {{ loading ? '检测中...' : '检测缺失关系' }}
        </Button>
      </div>
    </div>

    <div class="flex-1 overflow-hidden flex flex-col">
      <div v-if="fixes.length === 0" class="flex-1 flex flex-col items-center justify-center text-muted-foreground p-4 text-center">
        <ScanIcon class="h-8 w-8 mb-2 opacity-20" />
        <p class="text-xs">输入主节点和关键词<br>开始检测潜在的关系缺失</p>
      </div>
      
      <div v-else class="flex flex-col h-full">
        <div class="px-4 py-2 border-b bg-muted/20 flex justify-between items-center">
          <span class="text-xs font-medium text-muted-foreground">检测结果 ({{ fixes.length }})</span>
          <Button 
            variant="ghost" 
            size="sm" 
            class="h-6 text-[10px] px-2"
            @click="toggleAll"
          >
            {{ allSelected ? '取消全选' : '全选' }}
          </Button>
        </div>
        
        <ScrollArea class="flex-1">
          <div class="p-3 space-y-2">
            <div 
              v-for="(fix, idx) in fixes" 
              :key="idx" 
              class="flex items-start gap-3 p-3 rounded-md border bg-card hover:bg-accent/50 transition-colors shadow-sm"
            >
              <Checkbox 
                :checked="selectedFixes.includes(fix)"
                @update:checked="(checked) => toggleFix(fix, checked)"
                class="mt-0.5"
              />
              <div class="space-y-1 min-w-0 flex-1">
                <div class="text-xs font-medium leading-none flex items-center flex-wrap gap-1">
                  <span class="truncate max-w-[80px]" :title="fix.source">{{ fix.source }}</span>
                  <ArrowRightIcon class="h-3 w-3 text-muted-foreground flex-shrink-0" />
                  <span class="truncate max-w-[80px]" :title="fix.target">{{ fix.target }}</span>
                </div>
                <div class="text-[10px] text-muted-foreground line-clamp-2 bg-muted/50 p-1 rounded">
                  {{ fix.reason }}
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>
        
        <div class="p-4 border-t bg-background">
          <Button 
            class="w-full" 
            size="sm"
            @click="$emit('apply', selectedFixes)"
            :disabled="selectedFixes.length === 0 || loading"
          >
            修复选中 ({{ selectedFixes.length }})
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Scan as ScanIcon, ArrowRight as ArrowRightIcon } from 'lucide-vue-next';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { RelationFix } from '../api';

const props = defineProps<{
  fixes: RelationFix[];
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'detect', mainNode: string, keyword: string): void;
  (e: 'apply', fixes: RelationFix[]): void;
}>();

const localMainNode = ref('');
const localKeyword = ref('');
const selectedFixes = ref<RelationFix[]>([]);

const allSelected = computed(() => {
  return props.fixes.length > 0 && selectedFixes.value.length === props.fixes.length;
});

watch(() => props.fixes, (newFixes) => {
  selectedFixes.value = [...newFixes];
});

const handleDetect = () => {
  if (localMainNode.value && localKeyword.value) {
    emit('detect', localMainNode.value, localKeyword.value);
  }
};

const toggleFix = (fix: RelationFix, checked: boolean) => {
  if (checked) {
    if (!selectedFixes.value.includes(fix)) selectedFixes.value.push(fix);
  } else {
    const idx = selectedFixes.value.indexOf(fix);
    if (idx > -1) selectedFixes.value.splice(idx, 1);
  }
};

const toggleAll = () => {
  if (allSelected.value) {
    selectedFixes.value = [];
  } else {
    selectedFixes.value = [...props.fixes];
  }
};
</script>
