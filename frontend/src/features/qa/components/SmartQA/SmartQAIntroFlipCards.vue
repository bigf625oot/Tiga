<template>
  <div class="grid w-full grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
    <button
      type="button"
      class="group relative w-full h-[120px] [perspective:1000px] text-left"
      @click="emit('select', 'auto')"
    >
      <div class="relative w-full h-full transition-transform duration-500 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
        <Card
          class="absolute inset-0 rounded-xl overflow-hidden bg-white/60 dark:bg-card/40 backdrop-blur-md border transition-all duration-300 [backface-visibility:hidden]"
          :class="modeEntrance === 'auto' ? 'border-blue-500/60 ring-1 ring-blue-200 dark:ring-blue-900 shadow-md' : 'border-border/40 hover:shadow-xl hover:-translate-y-0.5'"
        >
          <div class="h-full w-full p-4 flex flex-col justify-between">
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-center gap-2 min-w-0">
                <div class="h-9 w-9 rounded-lg bg-blue-500/10 border border-blue-500/10 flex items-center justify-center">
                  <!-- <Bot class="w-4 h-4 text-blue-600 dark:text-blue-300" /> -->
                </div>
                <div class="min-w-0">
                  <div class="text-sm font-bold tracking-wide text-foreground truncate">秒懂</div>
                  <div class="text-xs text-muted-foreground truncate">大模型基于用户意图的自主执行</div>
                </div>
              </div>
              <div
                v-if="modeEntrance === 'auto'"
                class="rounded-full p-0.5 bg-blue-500 dark:bg-blue-500 animate-in fade-in zoom-in duration-200"
              >
                <Check class="w-3 h-3 text-white dark:text-slate-950" stroke-width="3" />
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="text-xs text-muted-foreground opacity-90 line-clamp-2">适合需求场景模糊的快速启动</div>
              <ArrowRight class="w-4 h-4 text-blue-600/60 dark:text-blue-300/60" />
            </div>
          </div>
        </Card>

        <Card
          class="absolute inset-0 rounded-xl overflow-hidden bg-gradient-to-b from-blue-50/80 to-white/80 dark:from-blue-950/30 dark:to-background/80 backdrop-blur-md border border-blue-500/30 [backface-visibility:hidden] [transform:rotateY(180deg)]"
        >
          <div class="h-full w-full p-4 flex flex-col justify-between">
            <div class="text-sm font-bold tracking-wide text-blue-700 dark:text-blue-300">AI秒懂</div>
            <div class="text-xs text-muted-foreground leading-relaxed opacity-90">
              自动选择能力与流程，减少手动配置
            </div>
            <div class="flex items-center gap-2 text-xs font-semibold text-blue-700 dark:text-blue-300">
              点击进入
              <ArrowRight class="w-3.5 h-3.5" />
            </div>
          </div>
        </Card>
      </div>
    </button>

    <button
      type="button"
      class="group relative w-full h-[120px] [perspective:1000px] text-left"
      @click="emit('select', 'manual')"
    >
      <div class="relative w-full h-full transition-transform duration-500 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
        <Card
          class="absolute inset-0 rounded-xl overflow-hidden bg-white/60 dark:bg-card/40 backdrop-blur-md border transition-all duration-300 [backface-visibility:hidden]"
          :class="modeEntrance === 'manual' ? 'border-purple-500/60 ring-1 ring-purple-200 dark:ring-purple-900 shadow-md' : 'border-border/40 hover:shadow-xl hover:-translate-y-0.5'"
        >
          <div class="h-full w-full p-4 flex flex-col justify-between">
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-center gap-2 min-w-0">
                <div class="h-9 w-9 rounded-lg bg-purple-500/10 border border-purple-500/10 flex items-center justify-center">
                  <!-- <Settings class="w-4 h-4 text-purple-600 dark:text-purple-300" /> -->
                </div>
                <div class="min-w-0">
                  <div class="text-sm font-bold tracking-wide text-foreground truncate">极客</div>
                  <div class="text-xs text-muted-foreground truncate">智能体自定义与精细控制</div>
                </div>
              </div>
              <div
                v-if="modeEntrance === 'manual'"
                class="rounded-full p-0.5 bg-purple-500 dark:bg-purple-500 animate-in fade-in zoom-in duration-200"
              >
                <Check class="w-3 h-3 text-white dark:text-slate-950" stroke-width="3" />
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="text-xs text-muted-foreground opacity-90 line-clamp-2">需求场景明确熟练使用智能体平台</div>
              <ArrowRight class="w-4 h-4 text-purple-600/60 dark:text-purple-300/60" />
            </div>
          </div>
        </Card>

        <Card
          class="absolute inset-0 rounded-xl overflow-hidden bg-gradient-to-b from-purple-50/80 to-white/80 dark:from-purple-950/30 dark:to-background/80 backdrop-blur-md border border-purple-500/30 [backface-visibility:hidden] [transform:rotateY(180deg)]"
        >
          <div class="h-full w-full p-4 flex flex-col justify-between">
            <div class="text-sm font-bold tracking-wide text-purple-700 dark:text-purple-300">手动 专业</div>
            <div class="text-xs text-muted-foreground leading-relaxed opacity-90">
              自由选择 Quick / Solo / 团队 / 工作流 / Openclaw
            </div>
            <div class="flex items-center gap-2 text-xs font-semibold text-purple-700 dark:text-purple-300">
              点击选择
              <ArrowRight class="w-3.5 h-3.5" />
            </div>
          </div>
        </Card>
      </div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight, Bot, Check, Settings } from 'lucide-vue-next';
import { Card } from '@/components/ui/card';

defineProps<{
  modeEntrance: 'auto' | 'manual';
}>();

const emit = defineEmits<{
  (e: 'select', next: 'auto' | 'manual'): void;
}>();
</script>
