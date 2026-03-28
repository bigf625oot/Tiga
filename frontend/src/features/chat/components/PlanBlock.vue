<script setup lang="ts">
import { CheckCircle2, Circle, Loader2, ListTodo } from 'lucide-vue-next';
import type { PlanBlock } from '../types';

defineProps<{
  block: PlanBlock;
}>();
</script>

<template>
  <div class="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
    <div class="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/20">
      <ListTodo class="w-4 h-4 text-primary" />
      <span class="text-sm font-medium">Execution Plan</span>
    </div>
    <div class="p-4 space-y-4">
      <div 
        v-for="(step, index) in block.steps" 
        :key="step.id"
        class="flex items-start gap-3 relative"
      >
        <!-- Connector Line -->
        <div 
          v-if="index < block.steps.length - 1" 
          class="absolute left-2.5 top-6 w-0.5 h-full -ml-[1px] bg-border"
        ></div>

        <!-- Status Icon -->
        <div class="relative z-10 bg-card rounded-full mt-0.5">
          <CheckCircle2 v-if="step.status === 'completed'" class="w-5 h-5 text-green-500" />
          <div v-else-if="step.status === 'running'" class="relative flex items-center justify-center w-5 h-5">
            <Loader2 class="w-5 h-5 text-blue-500 animate-spin absolute" />
            <div class="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse"></div>
          </div>
          <Circle v-else class="w-5 h-5 text-muted-foreground" />
        </div>

        <!-- Step Text -->
        <div 
          class="flex-1 text-sm pt-0.5 pb-2"
          :class="{
            'text-muted-foreground line-through opacity-70': step.status === 'completed',
            'text-foreground font-medium': step.status === 'running',
            'text-foreground/80': step.status === 'pending'
          }"
        >
          {{ step.text }}
        </div>
      </div>
    </div>
  </div>
</template>
