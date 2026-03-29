<template>
  <div class="mermaid-container my-2 rounded-lg border border-border bg-card overflow-x-auto">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-3 py-1.5 border-b border-border bg-muted/40">
      <span class="text-[11px] font-medium text-muted-foreground">流程图 / 图表</span>
      <div class="flex items-center gap-0.5">
        <span v-if="status === 'rendering'" class="text-[10px] text-muted-foreground animate-pulse mr-1">渲染中...</span>
        <span v-if="status === 'error'" class="text-[10px] text-destructive mr-1">渲染失败</span>
        <button
          v-if="status === 'done'"
          class="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          title="全屏查看"
          @click="openFullscreen"
        >
          <Expand class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Inline diagram with skeleton -->
    <div class="relative min-h-[120px] flex items-center justify-center p-4">
      <div v-if="status === 'rendering'" class="w-full flex flex-col items-center gap-3 py-4">
        <Skeleton class="h-6 w-48 rounded" />
        <div class="flex gap-8">
          <div class="flex flex-col gap-2">
            <Skeleton class="h-5 w-24 rounded" />
            <Skeleton class="h-5 w-32 rounded" />
          </div>
          <div class="flex flex-col gap-2">
            <Skeleton class="h-5 w-28 rounded" />
            <Skeleton class="h-5 w-20 rounded" />
          </div>
        </div>
        <Skeleton class="h-5 w-36 rounded mt-1" />
      </div>

      <div
        ref="mermaidRef"
        class="w-full transition-opacity duration-300"
        :class="status === 'rendering' ? 'opacity-0 absolute pointer-events-none' : 'opacity-100'"
      />

      <div
        v-if="status === 'error'"
        class="w-full text-xs text-destructive font-mono whitespace-pre-wrap bg-destructive/5 border border-destructive/20 rounded p-3"
      >{{ errorMsg }}</div>
    </div>

    <!-- Full-screen Dialog -->
    <Dialog v-model:open="isOpen">
      <DialogContent
        class="max-w-[94vw] w-[94vw] h-[90vh] flex flex-col p-0 gap-0 [&>button]:top-3 [&>button]:right-3"
      >
        <DialogHeader class="px-4 py-2.5 border-b border-border flex-shrink-0">
          <div class="flex items-center justify-between pr-6">
            <DialogTitle class="text-sm font-medium">流程图 / 图表</DialogTitle>
            <Button variant="ghost" size="icon" class="h-7 w-7" :title="copied ? '已复制' : '复制源码'" @click="copyCode">
              <Check v-if="copied" class="w-3.5 h-3.5 text-green-500" />
              <Copy v-else class="w-3.5 h-3.5" />
            </Button>
          </div>
        </DialogHeader>

        <Tabs v-model="activeTab" class="flex flex-col flex-1 min-h-0 overflow-hidden">
          <TabsList class="mx-4 mt-2 mb-0 w-fit flex-shrink-0 h-8">
            <TabsTrigger value="view" class="text-xs px-3 h-6">图表</TabsTrigger>
            <TabsTrigger value="source" class="text-xs px-3 h-6">Mermaid 源码</TabsTrigger>
          </TabsList>

          <TabsContent value="view" class="flex-1 min-h-0 m-0 overflow-auto">
            <div class="w-full h-full flex items-start justify-center p-6">
              <!-- Cloned SVG injected here by openFullscreen() -->
              <div ref="fullDiagramRef" class="w-full" />
            </div>
          </TabsContent>
          <TabsContent value="source" class="flex-1 min-h-0 m-0 overflow-auto">
            <pre class="p-4 text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-relaxed">{{ props.code }}</pre>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import mermaid from 'mermaid';
import { Expand, Copy, Check } from 'lucide-vue-next';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

// ── Module-level singleton init ────────────────────────────────────────────
let initialized = false;
const initMermaid = () => {
  if (initialized) return;
  initialized = true;
  const isDark = document.documentElement.classList.contains('dark');
  mermaid.initialize({
    startOnLoad: false,
    theme: isDark ? 'dark' : 'neutral',
    securityLevel: 'loose',
    fontFamily: 'inherit',
    fontSize: 14,
    flowchart: { curve: 'basis', padding: 20 },
    themeVariables: isDark ? {} : {
      // Clean neutral palette aligned with shadcn/ui slate tokens
      background:           '#ffffff',
      primaryColor:         '#f1f5f9',   // slate-100
      primaryTextColor:     '#1e293b',   // slate-800
      primaryBorderColor:   '#cbd5e1',   // slate-300
      secondaryColor:       '#f8fafc',   // slate-50
      secondaryTextColor:   '#475569',   // slate-600
      secondaryBorderColor: '#e2e8f0',   // slate-200
      tertiaryColor:        '#eff6ff',   // blue-50
      tertiaryTextColor:    '#1e40af',   // blue-800
      tertiaryBorderColor:  '#bfdbfe',   // blue-200
      lineColor:            '#94a3b8',   // slate-400
      edgeLabelBackground:  '#ffffff',
      clusterBkg:           '#f8fafc',
      clusterBorder:        '#e2e8f0',
      titleColor:           '#1e293b',
      nodeTextColor:        '#1e293b',
    },
  });
};

const props = defineProps<{ code: string }>();

const mermaidRef = ref<HTMLElement | null>(null);
const fullDiagramRef = ref<HTMLElement | null>(null);
const status = ref<'idle' | 'rendering' | 'done' | 'error'>('idle');
const errorMsg = ref('');
const isOpen = ref(false);
const activeTab = ref<'view' | 'source'>('view');
const copied = ref(false);

let renderSeq = 0;

// ── Inline render ─────────────────────────────────────────────────────────
const renderDiagram = async () => {
  if (!mermaidRef.value || !props.code?.trim()) { status.value = 'idle'; return; }
  const thisSeq = ++renderSeq;
  status.value = 'rendering';
  errorMsg.value = '';
  try {
    const { svg } = await mermaid.render(`mermaid-inline-${thisSeq}`, props.code.trim());
    if (thisSeq !== renderSeq) return;
    mermaidRef.value.innerHTML = svg;
    if (!mermaidRef.value.querySelector('svg')) throw new Error('Diagram rendered empty.');
    status.value = 'done';
  } catch (err: any) {
    if (thisSeq !== renderSeq) return;
    errorMsg.value = (typeof err === 'string' ? err : err?.message || 'Render failed').trim();
    status.value = 'error';
    if (mermaidRef.value) mermaidRef.value.innerHTML = '';
  }
};

// ── Fullscreen: clone already-rendered inline SVG — no async, no re-render ─
// This completely bypasses Portal/animation timing issues.
const injectFullSvg = () => {
  if (!fullDiagramRef.value || !mermaidRef.value) return;
  const inlineSvg = mermaidRef.value.querySelector('svg');
  if (!inlineSvg) return;
  // Deep clone the SVG and remove width constraints so it fills the dialog
  const clone = inlineSvg.cloneNode(true) as SVGElement;
  clone.style.maxWidth = 'none';
  clone.style.width = '100%';
  clone.style.height = 'auto';
  clone.removeAttribute('width');
  fullDiagramRef.value.innerHTML = '';
  fullDiagramRef.value.appendChild(clone);
};

const openFullscreen = () => {
  activeTab.value = 'view';
  isOpen.value = true;
};

// After dialog opens, wait for TabsContent to mount then inject SVG
watch(isOpen, async (open) => {
  if (!open) return;
  await nextTick();          // Vue reactive DOM flush
  await nextTick();          // Second tick: Radix Vue Portal settle
  injectFullSvg();
});

// Also re-inject when switching back to view tab
watch(activeTab, async (tab) => {
  if (tab !== 'view' || !isOpen.value) return;
  await nextTick();
  injectFullSvg();
});

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code ?? '');
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch { /* silently ignore */ }
};

watch(() => props.code, renderDiagram);

// ── Lifecycle ─────────────────────────────────────────────────────────────
onMounted(() => { initMermaid(); renderDiagram(); });
onBeforeUnmount(() => { renderSeq = Infinity; });
</script>

<style scoped>
.mermaid-container :deep(svg) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}
</style>
