<template>
  <div class="flex flex-col h-full overflow-hidden select-none" style="background:#525659;">
    <!-- Toolbar: renders immediately, no dependency on PDF load state -->
    <div class="flex items-center gap-2 px-3 h-10 shrink-0 text-white/90 text-xs z-10" style="background:#3d4043;">
      <!-- Page navigation -->
      <button
        class="flex items-center justify-center w-6 h-6 rounded hover:bg-white/10 transition-colors disabled:opacity-30"
        :disabled="!pdfLoaded || currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      >
        <ChevronUp class="w-3.5 h-3.5" />
      </button>

      <div class="flex items-center gap-1">
        <input
          v-model.number="pageInput"
          class="w-9 text-center bg-white/10 border border-white/20 rounded px-1 py-0.5 text-xs focus:outline-none focus:border-white/50 [appearance:textfield]"
          type="number"
          :min="1"
          :max="totalPages"
          :disabled="!pdfLoaded"
          @keydown.enter="jumpToPage"
          @blur="jumpToPage"
        />
        <span class="text-white/50">/</span>
        <span class="text-white/70 min-w-[1.5rem] text-center">
          {{ pdfLoaded ? totalPages : '—' }}
        </span>
      </div>

      <button
        class="flex items-center justify-center w-6 h-6 rounded hover:bg-white/10 transition-colors disabled:opacity-30"
        :disabled="!pdfLoaded || currentPage >= totalPages"
        @click="goToPage(currentPage + 1)"
      >
        <ChevronDown class="w-3.5 h-3.5" />
      </button>

      <div class="w-px h-4 bg-white/20 mx-1" />

      <!-- Zoom controls -->
      <button
        class="flex items-center justify-center w-6 h-6 rounded hover:bg-white/10 transition-colors disabled:opacity-30"
        :disabled="!pdfLoaded || scale <= 0.5"
        @click="adjustZoom(-0.25)"
      >
        <ZoomOut class="w-3.5 h-3.5" />
      </button>

      <span class="w-11 text-center tabular-nums">{{ Math.round(scale * 100) }}%</span>

      <button
        class="flex items-center justify-center w-6 h-6 rounded hover:bg-white/10 transition-colors disabled:opacity-30"
        :disabled="!pdfLoaded || scale >= 3"
        @click="adjustZoom(0.25)"
      >
        <ZoomIn class="w-3.5 h-3.5" />
      </button>

      <button
        class="flex items-center justify-center w-6 h-6 rounded hover:bg-white/10 transition-colors ml-1"
        title="适合宽度"
        :disabled="!pdfLoaded"
        @click="fitToWidth"
      >
        <Maximize2 class="w-3.5 h-3.5" />
      </button>

      <!-- Loading indicator -->
      <div v-if="!pdfLoaded && !loadError" class="flex items-center gap-1.5 ml-2 text-white/60">
        <Loader2 class="w-3 h-3 animate-spin" />
        <span>加载中...</span>
      </div>
      <div v-if="loadError" class="flex items-center gap-1.5 ml-2 text-red-400 text-[11px]">
        <span>{{ loadError }}</span>
      </div>
    </div>

    <!-- Pages scroll container -->
    <div ref="scrollContainerRef" class="flex-1 overflow-auto" @scroll="onScroll">
      <div class="flex flex-col items-center py-4 gap-4">
        <!-- Page skeletons (appear once numPages is known) -->
        <template v-if="pdfLoaded">
          <div
            v-for="n in totalPages"
            :key="n"
            :ref="el => registerPageEl(el as HTMLElement | null, n)"
            class="relative shadow-xl"
            :style="{ width: pageWidth(n) + 'px', height: pageHeight(n) + 'px' }"
          >
            <!-- Skeleton shown until page is rendered -->
            <div
              v-if="!renderedPages.has(n)"
              class="absolute inset-0 animate-pulse"
              style="background:#e5e5e5;"
            />
            <canvas
              v-show="renderedPages.has(n)"
              :ref="el => registerCanvas(el as HTMLCanvasElement | null, n)"
              class="block"
            />
          </div>
        </template>

        <!-- Initial skeleton before PDF loads -->
        <template v-else-if="!loadError">
          <div
            v-for="i in 3"
            :key="i"
            class="animate-pulse shadow-xl"
            :style="{ width: containerWidth * 0.85 + 'px', height: containerWidth * 0.85 * 1.414 + 'px', background:'#e5e5e5' }"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { ChevronUp, ChevronDown, ZoomIn, ZoomOut, Maximize2, Loader2 } from 'lucide-vue-next';
import * as pdfjsLib from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

const props = defineProps<{ src: string }>();

// ── State ─────────────────────────────────────────────────────────────────────
const scrollContainerRef = ref<HTMLElement | null>(null);
const pdfDoc = ref<any>(null);
const pdfLoaded = ref(false);
const loadError = ref('');
const totalPages = ref(0);
const currentPage = ref(1);
const pageInput = ref(1);
const scale = ref(1.2);
const containerWidth = ref(600);

// Per-page metadata (populated after first-page viewport is known)
const pageDimensions = new Map<number, { width: number; height: number }>();
const renderedPages = ref(new Set<number>());

// DOM refs
const pageEls = new Map<number, HTMLElement>();
const canvasEls = new Map<number, HTMLCanvasElement>();
const renderingPages = new Set<number>();

let observer: IntersectionObserver | null = null;

// ── Dimensions ────────────────────────────────────────────────────────────────
const pageWidth = (n: number) => pageDimensions.get(n)?.width ?? containerWidth.value * 0.85;
const pageHeight = (n: number) => pageDimensions.get(n)?.height ?? pageWidth(n) * 1.414;

// ── DOM registration ──────────────────────────────────────────────────────────
const registerPageEl = (el: HTMLElement | null, n: number) => {
  if (el) {
    pageEls.set(n, el);
    observer?.observe(el);
  }
};

const registerCanvas = (el: HTMLCanvasElement | null, n: number) => {
  if (el) canvasEls.set(n, el);
};

// ── PDF loading ───────────────────────────────────────────────────────────────
const loadPdf = async (src: string) => {
  if (!src) return;

  pdfLoaded.value = false;
  loadError.value = '';
  totalPages.value = 0;
  renderedPages.value = new Set();
  renderedPages.value = renderedPages.value; // trigger reactivity
  pageDimensions.clear();
  pageEls.clear();
  canvasEls.clear();
  renderingPages.clear();
  pdfDoc.value = null;

  try {
    const task = pdfjsLib.getDocument({
      url: src,
      withCredentials: false,
      rangeChunkSize: 65536, // 64KB chunks — first page renders without full download
      disableRange: false,
      disableStream: false,
    });
    const pdf = await task.promise;
    pdfDoc.value = pdf;
    totalPages.value = pdf.numPages;

    // Pre-compute dimensions for all pages using first page scale
    const firstPage = await pdf.getPage(1);
    const vp = firstPage.getViewport({ scale: scale.value });
    for (let i = 1; i <= pdf.numPages; i++) {
      pageDimensions.set(i, { width: vp.width, height: vp.height });
    }

    pdfLoaded.value = true;

    // Let Vue render page containers, then start observing
    await nextTick();
    setupObserver();
  } catch (e: any) {
    loadError.value = '文档加载失败，请重试';
    console.error('[PdfViewer] load error:', e);
  }
};

// ── IntersectionObserver for lazy per-page rendering ─────────────────────────
const setupObserver = () => {
  observer?.disconnect();
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const pageNum = parseInt((entry.target as HTMLElement).dataset.page || '0', 10);
        if (pageNum && !renderedPages.value.has(pageNum) && !renderingPages.has(pageNum)) {
          renderPage(pageNum);
        }
      }
    },
    { root: scrollContainerRef.value, rootMargin: '200px 0px' }
  );

  for (const [n, el] of pageEls) {
    el.dataset.page = String(n);
    observer.observe(el);
  }
};

const renderPage = async (pageNum: number) => {
  if (!pdfDoc.value || renderingPages.has(pageNum)) return;
  renderingPages.add(pageNum);

  try {
    const page = await pdfDoc.value.getPage(pageNum);
    const viewport = page.getViewport({ scale: scale.value });

    const canvas = canvasEls.get(pageNum);
    if (!canvas) return;

    canvas.width = viewport.width;
    canvas.height = viewport.height;

    const ctx = canvas.getContext('2d')!;
    await page.render({ canvasContext: ctx, viewport }).promise;

    const next = new Set(renderedPages.value);
    next.add(pageNum);
    renderedPages.value = next;
  } catch (e) {
    console.warn(`[PdfViewer] render page ${pageNum} failed:`, e);
  } finally {
    renderingPages.delete(pageNum);
  }
};

// ── Re-render all rendered pages on scale change ──────────────────────────────
const rerenderAll = async () => {
  if (!pdfDoc.value) return;

  // Recompute dimensions
  const firstPage = await pdfDoc.value.getPage(1);
  const vp = firstPage.getViewport({ scale: scale.value });
  for (let i = 1; i <= totalPages.value; i++) {
    pageDimensions.set(i, { width: vp.width, height: vp.height });
  }

  // Re-render already visible/rendered pages
  const prev = new Set(renderedPages.value);
  renderedPages.value = new Set(); // reset triggers skeleton
  renderingPages.clear();

  await nextTick();
  for (const n of prev) renderPage(n);
};

// ── Navigation & zoom ─────────────────────────────────────────────────────────
const goToPage = (n: number) => {
  const clamped = Math.max(1, Math.min(totalPages.value, n));
  currentPage.value = clamped;
  pageInput.value = clamped;
  const el = pageEls.get(clamped);
  el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const jumpToPage = () => {
  if (pageInput.value >= 1 && pageInput.value <= totalPages.value) {
    goToPage(pageInput.value);
  } else {
    pageInput.value = currentPage.value;
  }
};

const adjustZoom = (delta: number) => {
  scale.value = Math.max(0.5, Math.min(3, parseFloat((scale.value + delta).toFixed(2))));
  rerenderAll();
};

const fitToWidth = async () => {
  if (!pdfDoc.value || !scrollContainerRef.value) return;
  const page = await pdfDoc.value.getPage(1);
  const naturalVp = page.getViewport({ scale: 1 });
  const availableWidth = scrollContainerRef.value.clientWidth - 32; // 16px padding each side
  scale.value = parseFloat((availableWidth / naturalVp.width).toFixed(2));
  rerenderAll();
};

// Track current page based on scroll position
const onScroll = () => {
  if (!scrollContainerRef.value) return;
  const scrollTop = scrollContainerRef.value.scrollTop;
  let accumulated = 16; // initial padding
  for (let n = 1; n <= totalPages.value; n++) {
    const h = pageHeight(n);
    if (scrollTop < accumulated + h) {
      if (currentPage.value !== n) {
        currentPage.value = n;
        pageInput.value = n;
      }
      break;
    }
    accumulated += h + 16; // gap
  }
};

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
  if (scrollContainerRef.value) {
    containerWidth.value = scrollContainerRef.value.clientWidth;
  }
  if (props.src) loadPdf(props.src);
});

onUnmounted(() => {
  observer?.disconnect();
  pdfDoc.value?.destroy?.();
});

watch(() => props.src, (src) => {
  if (src) loadPdf(src);
  else {
    pdfLoaded.value = false;
    totalPages.value = 0;
    renderedPages.value = new Set();
  }
});
</script>
