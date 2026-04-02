<script setup lang="ts">
import { ref, computed } from 'vue';
import { FileEdit, FilePlus, FileMinus, Check, X } from 'lucide-vue-next';
import Button from '@/components/ui/button/Button.vue';
import Badge from '@/components/ui/badge/Badge.vue';
import type { ActionBlock } from '@/features/llm-chat/shared/types';

const props = defineProps<{
  block: ActionBlock;
}>();

const emit = defineEmits<{
  (e: 'apply', id: string): void;
  (e: 'discard', id: string): void;
}>();

const actionState = ref(props.block.status);

const isApplied = computed(() => actionState.value === 'applied');
const isRejected = computed(() => actionState.value === 'rejected');
const isLocked = computed(() => isApplied.value || isRejected.value);

const handleApply = () => {
  if (isLocked.value) return;
  actionState.value = 'applied';
  emit('apply', props.block.path);
};

const handleDiscard = () => {
  if (isLocked.value) return;
  actionState.value = 'rejected';
  emit('discard', props.block.path);
};

const parsedDiff = computed(() => {
  if (!props.block.diff) return [];
  const lines = props.block.diff.split('\n');
  return lines.map(line => {
    let type = 'normal';
    if (line.startsWith('+') && !line.startsWith('+++')) type = 'add';
    else if (line.startsWith('-') && !line.startsWith('---')) type = 'remove';
    else if (line.startsWith('@@')) type = 'header';
    return { text: line, type };
  });
});

const actionIcon = computed(() => {
  switch (props.block.action_type) {
    case 'create_file': return FilePlus;
    case 'delete_file': return FileMinus;
    default: return FileEdit;
  }
});

const actionLabel = computed(() => {
  switch (props.block.action_type) {
    case 'create_file': return 'New';
    case 'delete_file': return 'Delete';
    default: return 'Edit';
  }
});

const badgeVariant = computed(() => {
  switch (props.block.action_type) {
    case 'create_file': return 'default'; // often primary/green
    case 'delete_file': return 'destructive';
    default: return 'secondary'; // often blue/gray
  }
});
</script>

<template>
  <div 
    class="rounded-xl border border-border bg-card text-card-foreground shadow-sm overflow-hidden flex flex-col transition-all duration-300"
    :class="{ 'opacity-60 grayscale-[0.5]': isLocked }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/20">
      <div class="flex items-center gap-2 overflow-hidden">
        <component :is="actionIcon" class="w-4 h-4 text-muted-foreground shrink-0" />
        <span class="font-mono text-sm font-medium truncate">{{ block.path }}</span>
      </div>
      <Badge :variant="badgeVariant" class="ml-2 shrink-0">{{ actionLabel }}</Badge>
    </div>

    <!-- Diff Viewer -->
    <div class="max-h-[300px] overflow-y-auto bg-[#1e1e1e] p-4 text-sm font-mono leading-relaxed">
      <div 
        v-for="(line, index) in parsedDiff" 
        :key="index"
        class="whitespace-pre flex"
        :class="{
          'bg-green-900/30 text-green-400': line.type === 'add',
          'bg-red-900/30 text-red-400': line.type === 'remove',
          'text-blue-400': line.type === 'header',
          'text-gray-300': line.type === 'normal'
        }"
      >
        <span class="select-none opacity-50 w-6 shrink-0 text-right pr-2 text-xs leading-5">
          {{ line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' ' }}
        </span>
        <span class="break-all">{{ line.text }}</span>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/10">
      <div class="text-xs text-muted-foreground truncate mr-4">
        {{ block.description }}
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <Button 
          variant="outline" 
          size="sm" 
          @click="handleDiscard"
          :disabled="isLocked"
          class="h-8 text-xs"
        >
          <X class="w-3 h-3 mr-1" />
          Discard
        </Button>
        <Button 
          variant="default" 
          size="sm" 
          @click="handleApply"
          :disabled="isLocked"
          class="h-8 text-xs"
        >
          <Check class="w-3 h-3 mr-1" />
          {{ isApplied ? 'Applied' : 'Apply' }}
        </Button>
      </div>
    </div>
  </div>
</template>
