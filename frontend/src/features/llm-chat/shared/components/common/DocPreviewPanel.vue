<template>
  <Transition name="panel-slide">
    <div
      v-if="visible"
      class="flex flex-row h-full shrink-0 overflow-hidden"
      :style="{ width: panelWidth + 'px' }"
    >
      <!-- ── Carousel Resize Handle ─────────────────────────────────────────── -->
      <div
        class="w-6 h-full shrink-0 flex flex-col items-center justify-center gap-1.5
               cursor-col-resize select-none relative group
               hover:bg-primary/10 transition-colors duration-150 z-10"
        @mousedown="startCarouselDrag"
      >
        <!-- Left border indicator -->
        <div
          class="absolute inset-y-0 left-0 w-px bg-border
                 group-hover:bg-primary transition-all duration-150"
        />

        <!-- Prev (narrower) button -->
        <button
          class="flex items-center justify-center w-4 h-4 rounded
                 text-muted-foreground hover:text-foreground hover:bg-primary/20
                 transition-colors disabled:opacity-20 disabled:cursor-default"
          :disabled="presetIdx <= 0"
          title="缩小面板"
          @click.stop="stepPreset(-1)"
        >
          <ChevronLeft class="w-3 h-3" />
        </button>

        <!-- Dots — current preset indicator -->
        <div class="flex flex-col gap-1">
          <div
            v-for="(_, i) in PRESETS"
            :key="i"
            class="w-1 rounded-full transition-all duration-200"
            :class="[
              i === presetIdx
                ? 'h-2.5 bg-primary'
                : 'h-1 bg-border group-hover:bg-muted-foreground/40',
            ]"
          />
        </div>

        <!-- Next (wider) button -->
        <button
          class="flex items-center justify-center w-4 h-4 rounded
                 text-muted-foreground hover:text-foreground hover:bg-primary/20
                 transition-colors disabled:opacity-20 disabled:cursor-default"
          :disabled="presetIdx >= PRESETS.length - 1"
          title="放大面板"
          @click.stop="stepPreset(1)"
        >
          <ChevronRight class="w-3 h-3" />
        </button>
      </div>

      <!-- ── Panel Body ──────────────────────────────────────────────────────── -->
      <div class="flex flex-col flex-1 min-w-0 bg-background overflow-hidden border-l border-border">

        <!-- Header -->
        <div class="flex items-center gap-3 px-4 py-2.5 shrink-0 border-b border-border bg-muted/30">
          <!-- PDF Icon -->
          <div class="flex items-center justify-center w-7 h-7 rounded-md bg-destructive/10 border border-destructive/20 shrink-0">
            <svg class="w-4 h-4 text-destructive" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z"
                stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
              />
              <path d="M14 2V8H20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              <text x="6.5" y="17.5" font-family="Arial, sans-serif" font-size="5.5" font-weight="700" fill="currentColor" letter-spacing="0.3">PDF</text>
            </svg>
          </div>

          <!-- Title & ID -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-foreground truncate leading-snug" :title="filename || '文档预览'">
              {{ filename || '文档预览' }}
            </p>
            <p class="text-[11px] text-muted-foreground font-mono leading-snug">doc#{{ docId }}</p>
          </div>

          <!-- Action buttons: download + close -->
          <div class="flex items-center gap-1 shrink-0">
            <TooltipProvider :delay-duration="400">
              <Tooltip>
                <TooltipTrigger as-child>
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-7 w-7 text-muted-foreground hover:text-foreground"
                    as="a"
                    :href="pdfSrc || '#'"
                    :download="filename || true"
                    :aria-disabled="!pdfSrc"
                    aria-label="下载文档"
                  >
                    <Download class="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom"><p>下载文档</p></TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider :delay-duration="400">
              <Tooltip>
                <TooltipTrigger as-child>
                  <Button
                    variant="ghost"
                    size="icon"
                    class="h-7 w-7 text-muted-foreground hover:text-foreground"
                    aria-label="关闭预览"
                    @click="emit('close')"
                  >
                    <X class="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom"><p>关闭预览</p></TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>

        <!-- Body -->
        <div class="flex-1 relative overflow-hidden bg-muted/5">

          <!-- Loading state: Nielsen #1 Visibility of system status -->
          <Transition name="fade">
            <div
              v-if="uiState === 'loading'"
              class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-background/80 backdrop-blur-sm z-10 pointer-events-none"
            >
              <Loader2 class="w-6 h-6 animate-spin text-primary/60" />
              <span class="text-xs text-muted-foreground">加载文档中...</span>
            </div>
          </Transition>

          <!-- Error state: Nielsen #9 Help users recognize & recover from errors -->
          <Transition name="fade">
            <div
              v-if="uiState === 'error'"
              class="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6"
            >
              <div class="flex flex-col items-center gap-2 text-center">
                <div class="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center">
                  <AlertCircle class="w-5 h-5 text-destructive" />
                </div>
                <p class="text-sm font-medium text-foreground">文档加载失败</p>
                <p class="text-xs text-muted-foreground max-w-[200px]">文件无法读取，请尝试重新加载或直接下载</p>
              </div>
              <div class="flex items-center gap-2">
                <Button variant="outline" size="sm" class="h-8 text-xs gap-1.5" @click="reload">
                  <RefreshCw class="w-3 h-3" />
                  重新加载
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  class="h-8 text-xs gap-1.5"
                  as="a"
                  :href="`/api/v1/knowledge/${docId}/file`"
                  :download="filename || true"
                >
                  <Download class="w-3 h-3" />
                  下载文档
                </Button>
              </div>
            </div>
          </Transition>

          <!-- PDF viewer: <object type="application/pdf"> is used for native PDF rendering.
               The backend endpoint will redirect to an OSS presigned URL which natively
               supports HTTP Range and Content-Length, required by modern browser PDF viewers.
               Fallback slot provides a download link for environments without a PDF plugin. -->
          <object
            v-if="pdfSrc && uiState !== 'error'"
            :data="pdfSrc"
            type="application/pdf"
            class="w-full h-full border-none transition-opacity duration-300"
            :class="uiState === 'loading' ? 'opacity-0' : 'opacity-100'"
            aria-label="PDF 文档预览"
          >
            <div class="flex flex-col items-center justify-center h-full gap-4 p-6 text-center">
              <p class="text-sm text-muted-foreground">您的浏览器不支持内嵌 PDF 预览</p>
              <Button variant="outline" size="sm" class="gap-1.5" as="a" :href="pdfSrc" target="_blank">
                <ExternalLink class="w-3.5 h-3.5" />
                在新标签页中打开
              </Button>
            </div>
          </object>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { X, ChevronLeft, ChevronRight, Loader2, Download, AlertCircle, RefreshCw, ExternalLink } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { knowledgeService } from '@/features/llm-chat/shared/services/knowledgeService';

const props = defineProps<{
  visible: boolean;
  docId: string | number | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

// ── Carousel preset widths ────────────────────────────────────────────────────
const PRESETS = [360, 520, 760, 960, 1200] as const;
const DEFAULT_PRESET_IDX = 2; // 760px

const presetIdx = ref(DEFAULT_PRESET_IDX);
const panelWidth = ref<number>(PRESETS[DEFAULT_PRESET_IDX]);

const stepPreset = (dir: -1 | 1) => {
  const next = presetIdx.value + dir;
  if (next < 0 || next >= PRESETS.length) return;
  presetIdx.value = next;
  panelWidth.value = PRESETS[next];
};

// ── Carousel drag ─────────────────────────────────────────────────────────────
const DRAG_THRESHOLD = 40;
let dragStartX = 0;
let pendingStep = 0;

const onCarouselMouseMove = (e: MouseEvent) => {
  const delta = dragStartX - e.clientX;
  const newStep = delta > DRAG_THRESHOLD ? 1 : delta < -DRAG_THRESHOLD ? -1 : 0;
  if (newStep !== pendingStep) {
    pendingStep = newStep;
    const targetIdx = Math.max(0, Math.min(PRESETS.length - 1, presetIdx.value + newStep));
    panelWidth.value = PRESETS[targetIdx];
  }
};

const onCarouselMouseUp = () => {
  document.removeEventListener('mousemove', onCarouselMouseMove);
  document.removeEventListener('mouseup', onCarouselMouseUp);
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
  if (pendingStep !== 0) {
    const committed = Math.max(0, Math.min(PRESETS.length - 1, presetIdx.value + pendingStep));
    presetIdx.value = committed;
    panelWidth.value = PRESETS[committed];
  } else {
    panelWidth.value = PRESETS[presetIdx.value];
  }
  pendingStep = 0;
};

const startCarouselDrag = (e: MouseEvent) => {
  e.preventDefault();
  dragStartX = e.clientX;
  pendingStep = 0;
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
  document.addEventListener('mousemove', onCarouselMouseMove);
  document.addEventListener('mouseup', onCarouselMouseUp);
};

// ── PDF state machine ─────────────────────────────────────────────────────────
// 'idle'    → panel hidden or no doc selected
// 'loading' → preflight + meta fetch in progress; spinner shown, object hidden
// 'ready'   → object visible; loading spinner faded out
// 'error'   → preflight failed; error card shown
type PdfState = 'idle' | 'loading' | 'ready' | 'error';
const uiState = ref<PdfState>('idle');
const filename = ref('');
const pdfSrc = ref('');
let loadingTimer: ReturnType<typeof setTimeout> | undefined;

// <object type="application/pdf"> does not reliably fire load/error events
// in Chromium-based browsers because the PDF plugin runs out-of-process.
// After a reasonable timeout we optimistically dismiss the spinner — the PDF
// is almost certainly rendering at that point. Real failures are caught by
// the preflight HEAD request executed before setting pdfSrc.
const LOADING_TIMEOUT_MS = 10_000;

const startLoadingTimer = () => {
  clearTimeout(loadingTimer);
  loadingTimer = setTimeout(() => { uiState.value = 'ready'; }, LOADING_TIMEOUT_MS);
};

// Pre-flight GET: validate URL before mounting the <object>.
// HEAD is not forwarded by Vite's dev proxy (405), so we use GET with an
// AbortController — fetch resolves once response headers arrive (before body),
// letting us read res.ok / res.redirected and then discard the body.
const preflight = async (url: string): Promise<boolean> => {
  const ac = new AbortController();
  try {
    const res = await fetch(url, { signal: ac.signal, cache: 'no-store' });
    ac.abort(); // headers received; discard body to avoid downloading the PDF
    return res.ok || res.redirected;
  } catch (e: unknown) {
    if ((e as DOMException)?.name === 'AbortError') return false;
    return false;
  }
};

const reload = () => {
  if (!props.docId) return;
  pdfSrc.value = '';
  uiState.value = 'loading';
  // Brief tick to unmount the object before remounting with the same src
  setTimeout(async () => {
    const url = `/api/v1/knowledge/${props.docId}/file?t=${Date.now()}`;
    const preflightUrl = `${url}&_preflight=1`;
    const ok = await preflight(preflightUrl);
    if (!ok) { uiState.value = 'error'; return; }
    pdfSrc.value = url;
    startLoadingTimer();
  }, 50);
};

watch(
  () => [props.visible, props.docId] as const,
  async ([visible, docId]) => {
    clearTimeout(loadingTimer);
    if (!visible || !docId) {
      pdfSrc.value = '';
      filename.value = '';
      uiState.value = 'idle';
      return;
    }

    uiState.value = 'loading';
    const url = `/api/v1/knowledge/${docId}/file`;

    // Run preflight and meta fetch in parallel to minimise perceived latency
    // Append a query parameter to the preflight URL to prevent the browser from caching
    // the aborted response and serving it to the <object> tag.
    const preflightUrl = url.includes('?') ? `${url}&_preflight=1` : `${url}?_preflight=1`;
    const [ok] = await Promise.all([
      preflight(preflightUrl),
      knowledgeService.getDocMeta(docId)
        .then(meta => { filename.value = meta.filename ?? `doc#${docId}`; })
        .catch(() => { filename.value = `doc#${docId}`; }),
    ]);

    if (!ok) {
      uiState.value = 'error';
      return;
    }

    pdfSrc.value = url;
    startLoadingTimer();
  },
  { immediate: true }
);

onUnmounted(() => {
  clearTimeout(loadingTimer);
  document.removeEventListener('mousemove', onCarouselMouseMove);
  document.removeEventListener('mouseup', onCarouselMouseUp);
});
</script>

<style scoped>
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.2s ease;
  overflow: hidden;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  width: 0 !important;
  opacity: 0;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
