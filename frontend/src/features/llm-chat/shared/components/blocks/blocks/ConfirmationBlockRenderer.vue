<template>
  <div class="my-4 rounded-lg border bg-card shadow-sm overflow-hidden transition-all duration-300">
    <!-- Header: Status indicator -->
    <div 
      class="flex items-center gap-2 px-4 py-3 border-b"
      :class="{
        'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400': isPending,
        'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400': isApproved,
        'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400': isDenied,
        'bg-slate-500/10 border-slate-500/20 text-slate-700 dark:text-slate-400': isExpired
      }"
    >
      <ShieldAlert v-if="isPending" class="h-5 w-5" />
      <CheckCircle2 v-else-if="isApproved" class="h-5 w-5" />
      <XCircle v-else-if="isDenied" class="h-5 w-5" />
      <Clock v-else class="h-5 w-5" />
      
      <span class="font-medium text-sm">{{ statusText }}</span>
    </div>

    <!-- Content -->
    <div class="p-4 space-y-4">
      <div class="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
        {{ block.message }}
      </div>
      
      <!-- Actions (only visible when pending) -->
      <div v-if="isPending" class="flex gap-3 pt-2">
        <Button 
          variant="default" 
          class="flex-1 bg-amber-600 hover:bg-amber-700 text-white"
          :disabled="isSubmitting"
          @click="handleAction('approved')"
        >
          <Check class="w-4 h-4 mr-2" />
          允许执行 (Approve)
        </Button>
        <Button 
          variant="outline" 
          class="flex-1"
          :disabled="isSubmitting"
          @click="handleAction('denied')"
        >
          <X class="w-4 h-4 mr-2" />
          拒绝 (Deny)
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ShieldAlert, CheckCircle2, XCircle, Clock, Check, X } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import type { ConfirmationBlock } from '@/features/llm-chat/shared/types';
// Note: In a real app, this API call would be mapped to a proper service
// import { api } from '@/core/api/client';

const props = defineProps<{
  block: ConfirmationBlock;
}>();

const emit = defineEmits<{
  (e: 'action', status: 'approved' | 'denied', actionId: string): void;
}>();

// Ensure local reactivity if backend doesn't update immediately
const localStatus = ref(props.block.status || 'pending');
const isSubmitting = ref(false);

const isPending = computed(() => localStatus.value === 'pending');
const isApproved = computed(() => localStatus.value === 'approved');
const isDenied = computed(() => localStatus.value === 'denied');
const isExpired = computed(() => localStatus.value === 'expired');

const statusText = computed(() => {
  switch (localStatus.value) {
    case 'pending': return '需要人工授权 (Action Required)';
    case 'approved': return '已授权 (Approved)';
    case 'denied': return '已拒绝 (Denied)';
    case 'expired': return '已过期 (Expired)';
    default: return '未知状态';
  }
});

const handleAction = async (status: 'approved' | 'denied') => {
  if (!props.block.action_id || !isPending.value) return;
  
  isSubmitting.value = true;
  try {
    // 模拟后端调用
    // await api.post(`/chat/action/${props.block.action_id}/${status}`);
    
    // 乐观更新 UI
    localStatus.value = status;
    emit('action', status, props.block.action_id);
  } catch (error) {
    console.error('Failed to submit confirmation:', error);
  } finally {
    isSubmitting.value = false;
  }
};
</script>
