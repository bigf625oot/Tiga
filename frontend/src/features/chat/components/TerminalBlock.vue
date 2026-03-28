<script setup lang="ts">
import { Terminal as TerminalIcon } from 'lucide-vue-next';
import type { TerminalBlock } from '../types';

defineProps<{
  block: TerminalBlock;
}>();
</script>

<template>
  <div class="rounded-xl border border-border shadow-sm overflow-hidden flex flex-col bg-[#0d0d0d] text-gray-300">
    <!-- Header -->
    <div class="flex items-center gap-2 px-4 py-2 border-b border-gray-800 bg-[#1a1a1a]">
      <TerminalIcon class="w-4 h-4 text-gray-400" />
      <span class="text-xs font-mono text-gray-400">Terminal</span>
      <div class="ml-auto flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-gray-600"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-gray-600"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-gray-600"></div>
      </div>
    </div>

    <!-- Content -->
    <div class="p-4 font-mono text-sm overflow-x-auto leading-relaxed">
      <div class="flex items-center gap-2 mb-2 text-green-400">
        <span class="select-none">$</span>
        <span>{{ block.command }}</span>
      </div>
      <div class="text-gray-300 whitespace-pre-wrap">
        {{ block.output }}
        <span 
          v-if="block.status === 'running'" 
          class="inline-block w-2 h-4 bg-gray-400 align-middle ml-1 animate-pulse"
        ></span>
      </div>
    </div>
  </div>
</template>
