import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { DEFAULT_SPLIT_RATIO, STORAGE_KEYS } from '../constants';

/**
 * Manages the layout of the SmartQA component, including the split pane ratio,
 * collapse state of side panels, and responsive behavior.
 * 
 * @returns Layout state and control functions
 */
export function useSmartQALayout() {
  const isLeftCollapsed = ref(false);
  const isRightCollapsed = ref(false);
  const isDesktop = ref(false);
  const splitRatio = ref(DEFAULT_SPLIT_RATIO);
  const splitContainerRef = ref<HTMLElement | null>(null);

  const readSplitRatio = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.SPLIT_RATIO);
      const val = raw ? Number(raw) : NaN;
      if (!Number.isFinite(val)) return DEFAULT_SPLIT_RATIO;
      return Math.min(0.8, Math.max(0.2, val));
    } catch {
      return DEFAULT_SPLIT_RATIO;
    }
  };

  const writeSplitRatio = (val: number) => {
    try { localStorage.setItem(STORAGE_KEYS.SPLIT_RATIO, String(val)); } catch { }
  };

  const updateIsDesktop = () => {
    if (typeof window === 'undefined') return;
    isDesktop.value = window.matchMedia('(min-width: 1280px)').matches;
  };

  const leftPaneStyle = computed(() => {
    if (!isDesktop.value) return {};
    if (isLeftCollapsed.value) return { width: '0', flex: '0 0 0', overflow: 'hidden' };
    if (isRightCollapsed.value) return { width: '100%', flex: '1 1 100%' };
    const pct = Math.round(splitRatio.value * 10000) / 100;
    return { flex: `0 0 ${pct}%`, width: `${pct}%`, maxWidth: `${pct}%` };
  });

  const rightPaneStyle = computed(() => {
    if (!isDesktop.value) return {};
    if (isRightCollapsed.value) return { width: '0', flex: '0 0 0', overflow: 'hidden' };
    if (isLeftCollapsed.value) return { width: '100%', flex: '1 1 100%' };
    const pct = Math.round((1 - splitRatio.value) * 10000) / 100;
    return { flex: `0 0 ${pct}%`, width: `${pct}%`, maxWidth: `${pct}%` };
  });

  const toggleLeftPane = () => {
    if (isLeftCollapsed.value) {
      isLeftCollapsed.value = false;
      return;
    }
    if (isRightCollapsed.value) isRightCollapsed.value = false;
    isLeftCollapsed.value = true;
  };

  const toggleRightPane = () => {
    if (isRightCollapsed.value) {
      isRightCollapsed.value = false;
      return;
    }
    if (isLeftCollapsed.value) isLeftCollapsed.value = false;
    isRightCollapsed.value = true;
  };

  let isResizing = false;
  let resizeStartX = 0;
  let resizeStartRatio = DEFAULT_SPLIT_RATIO;
  let rafId: number | null = null;

  const onResizeMove = (e: MouseEvent) => {
    if (!isResizing) return;
    
    if (rafId) cancelAnimationFrame(rafId);
    
    rafId = requestAnimationFrame(() => {
      const el = splitContainerRef.value;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const delta = e.clientX - resizeStartX;
      const next = resizeStartRatio + (delta / rect.width);
      splitRatio.value = Math.min(0.8, Math.max(0.2, next));
    });
  };

  const stopResize = () => {
    if (!isResizing) return;
    isResizing = false;
    if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
    }
    window.removeEventListener('mousemove', onResizeMove);
    window.removeEventListener('mouseup', stopResize);
    writeSplitRatio(splitRatio.value);
  };

  const startResize = (e: MouseEvent) => {
    if (!isDesktop.value || isLeftCollapsed.value || isRightCollapsed.value) return;
    const el = splitContainerRef.value;
    if (!el) return;
    e.preventDefault();
    isResizing = true;
    resizeStartX = e.clientX;
    resizeStartRatio = splitRatio.value;
    window.addEventListener('mousemove', onResizeMove);
    window.addEventListener('mouseup', stopResize);
  };

  onMounted(() => {
    splitRatio.value = readSplitRatio();
    updateIsDesktop();
    window.addEventListener('resize', updateIsDesktop);
  });

  onBeforeUnmount(() => {
    window.removeEventListener('resize', updateIsDesktop);
    stopResize();
  });

  return {
    isLeftCollapsed,
    isRightCollapsed,
    isDesktop,
    splitRatio,
    splitContainerRef,
    leftPaneStyle,
    rightPaneStyle,
    toggleLeftPane,
    toggleRightPane,
    startResize
  };
}
