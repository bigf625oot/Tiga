<template>
  <div class="h-full flex flex-col bg-slate-50">
     <!-- Stats Header -->
     <div class="bg-white p-4 border-b border-slate-200 flex items-center gap-6 shadow-sm z-10">
        <div class="flex flex-col">
            <span class="text-xs text-slate-500">任务进度</span>
            <div class="flex items-center gap-2">
                <div class="w-32 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div class="h-full bg-indigo-500 transition-all duration-500" :style="{ width: store.progress + '%' }"></div>
                </div>
                <span class="text-sm font-bold text-indigo-600">{{ store.progress }}%</span>
            </div>
        </div>
        
        <div class="h-8 w-px bg-slate-200"></div>
        
        <div class="flex gap-4">
             <div class="flex flex-col">
                 <span class="text-xs text-slate-500">当前步骤</span>
                 <span class="text-sm font-medium text-slate-700">{{ store.currentStep || 'Ready' }}</span>
             </div>
             <div class="flex flex-col">
                 <span class="text-xs text-slate-500">状态</span>
                 <span class="text-sm font-medium" :class="store.isRunning ? 'text-blue-600' : 'text-slate-600'">
                    {{ store.isRunning ? '执行中...' : '空闲' }}
                 </span>
             </div>
        </div>
        
        <div class="flex-1"></div>
        
        <!-- Controls -->
        <div class="flex gap-2">
             <button v-if="store.isRunning" @click="store.stopWorkflow" class="px-3 py-1.5 bg-red-50 text-red-600 border border-red-100 rounded hover:bg-red-100 text-sm">
                 停止执行
             </button>
        </div>
     </div>
     
     <!-- Main Content -->
     <div class="flex-1 flex overflow-hidden">
        <!-- Left: Task Tree -->
        <div class="w-1/2 p-4 overflow-y-auto border-r border-slate-200 bg-white">
            <h3 class="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                <svg class="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>
                任务规划
            </h3>
            <TaskTree :tasks="store.tasks" />
        </div>
        
        <!-- Right: Logs -->
        <div class="w-1/2 p-4 bg-slate-900 overflow-hidden flex flex-col">
            <LogPanel :logs="store.logs" class="flex-1" />
        </div>
     </div>
  </div>
</template>

<script setup>
import { useWorkflowStore } from '../store/workflow.store';
import TaskTree from './TaskTree.vue';
import LogPanel from './LogPanel.vue';

const store = useWorkflowStore();
</script>
