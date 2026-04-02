<template>
  <div class="markmap-card border border-border rounded-lg bg-card overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-3 py-1.5 border-b border-border bg-muted/40">
      <span class="text-[11px] font-medium text-muted-foreground flex items-center gap-1.5">
        <GitBranch class="w-3 h-3" />
        思维导图
      </span>
      <div class="flex items-center gap-0.5">
        <button
          class="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
          title="适应视图"
          :disabled="!inlineReady"
          @click="fitInline"
        >
          <Scan class="w-3.5 h-3.5" />
        </button>
        <button
          class="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          title="全屏查看"
          @click="openDialog"
        >
          <Expand class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Inline preview -->
    <div class="relative w-full h-[640px] overflow-hidden">
      <!-- Skeleton while first render -->
      <div v-if="!inlineReady && props.content?.trim()" class="absolute inset-0 p-6 flex flex-col gap-4">
        <div class="flex justify-center">
          <Skeleton class="h-8 w-32 rounded-full" />
        </div>
        <div class="flex justify-between px-4 mt-2">
          <div class="flex flex-col gap-2.5">
            <Skeleton class="h-5 w-24 rounded" />
            <Skeleton class="h-5 w-20 rounded ml-5" />
            <Skeleton class="h-5 w-28 rounded ml-5" />
            <Skeleton class="h-5 w-18 rounded" />
            <Skeleton class="h-5 w-22 rounded ml-5" />
          </div>
          <div class="flex flex-col gap-2.5 items-end">
            <Skeleton class="h-5 w-22 rounded" />
            <Skeleton class="h-5 w-16 rounded mr-5" />
            <Skeleton class="h-5 w-28 rounded mr-5" />
            <Skeleton class="h-5 w-20 rounded" />
            <Skeleton class="h-5 w-24 rounded mr-5" />
          </div>
        </div>
      </div>

      <div
        v-if="!props.content?.trim()"
        class="absolute inset-0 flex items-center justify-center text-muted-foreground text-xs"
      >无内容</div>

      <svg
        ref="inlineSvgRef"
        class="w-full h-full transition-opacity duration-300"
        :class="inlineReady ? 'opacity-100' : 'opacity-0'"
      />
    </div>

    <!-- Full-screen Dialog -->
    <Dialog v-model:open="isOpen">
      <DialogContent
        class="max-w-[94vw] w-[94vw] h-[90vh] flex flex-col p-0 gap-0 [&>button]:top-3 [&>button]:right-3"
      >
        <DialogHeader class="px-4 py-2.5 border-b border-border flex-shrink-0">
          <div class="flex items-center justify-between pr-6">
            <DialogTitle class="text-sm font-medium flex items-center gap-2">
              <GitBranch class="w-4 h-4 text-primary" />
              思维导图
            </DialogTitle>
            <div class="flex items-center gap-1">
              <Button variant="ghost" size="icon" class="h-7 w-7" title="适应视图" @click="fitFull">
                <Scan class="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="ghost" size="icon" class="h-7 w-7"
                :title="copied ? '已复制' : '复制源码'"
                @click="copyCode"
              >
                <Check v-if="copied" class="w-3.5 h-3.5 text-green-500" />
                <Copy v-else class="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <Tabs v-model="activeTab" class="flex flex-col flex-1 min-h-0 overflow-hidden">
          <TabsList class="mx-4 mt-2 mb-0 w-fit flex-shrink-0 h-8">
            <TabsTrigger value="view" class="text-xs px-3 h-6">图表</TabsTrigger>
            <TabsTrigger value="source" class="text-xs px-3 h-6">Markdown 源码</TabsTrigger>
          </TabsList>

          <TabsContent value="view" class="flex-1 min-h-0 m-0 p-0 overflow-hidden relative">
            <!-- Skeleton while markmap initializes -->
            <div v-if="!fullReady" class="absolute inset-0 flex flex-col items-center justify-center gap-5 p-10">
              <Skeleton class="h-10 w-44 rounded-full" />
              <div class="flex gap-20 mt-2">
                <div class="flex flex-col gap-3">
                  <Skeleton class="h-6 w-32 rounded" />
                  <Skeleton class="h-6 w-40 rounded ml-6" />
                  <Skeleton class="h-6 w-28 rounded ml-6" />
                  <Skeleton class="h-6 w-36 rounded" />
                  <Skeleton class="h-6 w-24 rounded ml-6" />
                </div>
                <div class="flex flex-col gap-3 items-end">
                  <Skeleton class="h-6 w-36 rounded" />
                  <Skeleton class="h-6 w-28 rounded mr-6" />
                  <Skeleton class="h-6 w-44 rounded mr-6" />
                  <Skeleton class="h-6 w-32 rounded" />
                  <Skeleton class="h-6 w-20 rounded mr-6" />
                </div>
              </div>
            </div>
            <svg
              ref="fullSvgRef"
              class="w-full h-full transition-opacity duration-300"
              :class="fullReady ? 'opacity-100' : 'opacity-0'"
            />
          </TabsContent>
          <TabsContent value="source" class="flex-1 min-h-0 m-0 overflow-auto">
            <pre class="p-4 text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-relaxed">{{ props.content }}</pre>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { Transformer } from 'markmap-lib';
import { Markmap } from 'markmap-view';
import { GitBranch, Scan, Expand, Copy, Check } from 'lucide-vue-next';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

const props = defineProps<{ content: string }>();

// ── Singleton transformer ──────────────────────────────────────────────────
const transformer = new Transformer();

const MARKMAP_OPTIONS = {
  zoom: true,
  pan: true,
  fitRatio: 0.95,
  colorFreezeLevel: 2,   // siblings at depth≤2 share a hue; children inherit it
  nodeMinHeight: 18,
  spacingVertical: 10,
  spacingHorizontal: 100,
};

const inlineSvgRef = ref<SVGElement | null>(null);
const fullSvgRef = ref<SVGElement | null>(null);
let inlineMap: Markmap | null = null;
let fullMap: Markmap | null = null;

const isOpen = ref(false);
const activeTab = ref<'view' | 'source'>('view');
const copied = ref(false);
const inlineReady = ref(false);
const fullReady = ref(false);

const buildRoot = () => {
  if (!props.content?.trim()) return null;
  try {
    const { root } = transformer.transform(props.content.trim());
    return root;
  } catch { return null; }
};

// ── Inline render ─────────────────────────────────────────────────────────
const renderInline = () => {
  const root = buildRoot();
  if (!inlineSvgRef.value || !root) return;
  inlineReady.value = false;
  if (inlineMap) {
    inlineMap.setData(root);
  } else {
    inlineMap = Markmap.create(inlineSvgRef.value, MARKMAP_OPTIONS, root);
  }
  // fit() after browser has laid out the SVG with real dimensions
  requestAnimationFrame(() => {
    inlineMap?.fit();
    inlineReady.value = true;
  });
};

// ── Full-screen render ────────────────────────────────────────────────────
const renderFull = () => {
  const el = fullSvgRef.value;
  const root = buildRoot();
  if (!el || !root) return;
  fullReady.value = false;
  if (fullMap) {
    fullMap.setData(root);
  } else {
    fullMap = Markmap.create(el, MARKMAP_OPTIONS, root);
  }
  // Second rAF: Markmap's D3 layout + fit() both need real dimensions
  requestAnimationFrame(() => {
    if (!fullSvgRef.value) return;
    fullMap?.fit();
    fullReady.value = true;
  });
};

const fitInline = () => inlineMap?.fit();
const fitFull = () => fullMap?.fit();

const openDialog = () => {
  activeTab.value = 'view';
  isOpen.value = true;
};

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.content ?? '');
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch { /* silently ignore */ }
};

// ── Watchers ──────────────────────────────────────────────────────────────

// Watch the dialog open state.
// Dialog has a 200ms CSS animation — wait for it to finish before rendering
// so the SVG has real dimensions when Markmap calculates the D3 layout.
watch(isOpen, async (open) => {
  if (!open) {
    fullMap?.destroy();
    fullMap = null;
    fullReady.value = false;
    return;
  }
  await nextTick();
  await nextTick();
  setTimeout(renderFull, 220); // outlasts the dialog's duration-200 animation
});

// Re-render when switching back to view tab
watch(activeTab, async (tab) => {
  if (tab !== 'view' || !isOpen.value) return;
  await nextTick();
  setTimeout(renderFull, 50);
});

watch(
  () => props.content,
  () => {
    renderInline();
    if (isOpen.value && fullMap) {
      const root = buildRoot();
      if (root) { fullMap.setData(root); fullMap.fit(); }
    }
  }
);

// ── Lifecycle ─────────────────────────────────────────────────────────────
onMounted(async () => {
  await nextTick(); // ensure SVG element has real layout dimensions
  renderInline();
});
onBeforeUnmount(() => {
  inlineMap?.destroy();
  fullMap?.destroy();
});
</script>
