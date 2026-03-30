<template>
  <!-- 
    Claude 风格 Artifact 卡片
    核心定位：高信噪比、平滑过渡的交互式卡片，作为触发右侧面板的锚点。
  -->
  <div 
    class="group relative flex items-center justify-between p-3.5 w-full max-w-sm rounded-xl border border-slate-200/80 bg-white shadow-sm transition-all duration-300 ease-out hover:border-indigo-300 hover:shadow-md cursor-pointer overflow-hidden"
    @click="handleOpenArtifact"
  >
    <!-- 左侧内容区 -->
    <div class="flex items-center gap-4 min-w-0">
      
      <!-- 动态 Icon 容器 -->
      <div 
        class="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg transition-colors duration-300"
        :class="iconContainerClass"
      >
        <component :is="artifactIcon" class="w-5 h-5" :class="iconColorClass" />
      </div>

      <!-- 文本与元数据区 -->
      <div class="flex flex-col min-w-0">
        <h4 class="text-[14px] font-semibold text-slate-800 truncate leading-snug">
          {{ title }}
        </h4>
        <p class="text-[12px] text-slate-500 truncate mt-0.5 flex items-center gap-1.5">
          <span class="font-medium" :class="typeColorClass">{{ artifactTypeDisplay }}</span>
          <span v-if="metadata" class="text-slate-300">•</span>
          <span v-if="metadata">{{ metadata }}</span>
        </p>
      </div>
    </div>

    <!-- 右侧交互暗示区 (Hover 时平滑浮现，加载时显示 Loader) -->
    <div class="flex-shrink-0 pl-2">
      <div v-if="isLoading" class="p-1.5 rounded-md bg-slate-100 text-slate-400">
        <Loader2Icon class="w-4 h-4 animate-spin" />
      </div>
      <div v-else class="opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
        <div class="p-1.5 rounded-md bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-600">
          <Maximize2Icon class="w-4 h-4" />
        </div>
      </div>
    </div>
    
    <!-- 底部高光进度条暗示 (微视觉细节) -->
    <div class="absolute bottom-0 left-0 h-[2px] bg-indigo-500 w-0 group-hover:w-full transition-all duration-500 ease-out opacity-0 group-hover:opacity-100"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { 
  Code2Icon, 
  FileTextIcon, 
  FileJsonIcon, 
  TerminalIcon, 
  Image as ImageIcon,
  Maximize2Icon,
  Loader2Icon,
  FileIcon
} from 'lucide-vue-next';
import { useArtifact } from '@/features/llm-chat/shared/context/ArtifactContext';

const { openArtifact: contextOpenArtifact } = useArtifact();

const props = defineProps<{
  /** 产物标题，如 "Data Processing Script" 或 "index.ts" */
  title: string;
  /** 产物类型：code, markdown, json, image, pdf 等 */
  type: 'code' | 'markdown' | 'json' | 'shell' | 'image' | 'pdf' | string;
  /** 核心内容，用于传递给右侧面板展示 */
  content: string;
  /** 远程文件 URL（content 为空时优先从 URL 拉取内容） */
  url?: string;
  /** 附加元数据，如 "120 lines", "15 KB" */
  metadata?: string;
  /** 具体编程语言，如果是代码的话，如 "python", "vue" */
  language?: string;
}>();

const isLoading = ref(false);

// --- 动态视觉映射引擎 (Strategy Pattern) ---

// 1. 图标映射策略
const artifactIcon = computed(() => {
  switch (props.type) {
    case 'code': return Code2Icon;
    case 'json': return FileJsonIcon;
    case 'shell': return TerminalIcon;
    case 'image': return ImageIcon;
    case 'pdf': return FileTextIcon;
    case 'markdown':
    default: return FileIcon;
  }
});

// 2. 背景色映射策略
const iconContainerClass = computed(() => {
  switch (props.type) {
    case 'code': return 'bg-amber-50 group-hover:bg-amber-100';
    case 'json': return 'bg-emerald-50 group-hover:bg-emerald-100';
    case 'shell': return 'bg-slate-100 group-hover:bg-slate-200';
    case 'markdown': return 'bg-indigo-50 group-hover:bg-indigo-100';
    default: return 'bg-blue-50 group-hover:bg-blue-100';
  }
});

// 3. 图标颜色映射策略
const iconColorClass = computed(() => {
  switch (props.type) {
    case 'code': return 'text-amber-600';
    case 'json': return 'text-emerald-600';
    case 'shell': return 'text-slate-700';
    case 'markdown': return 'text-indigo-600';
    default: return 'text-blue-600';
  }
});

// 4. 类型文字颜色
const typeColorClass = computed(() => {
  switch (props.type) {
    case 'code': return 'text-amber-700';
    case 'markdown': return 'text-indigo-700';
    default: return 'text-slate-600';
  }
});

// 5. 显示文本格式化
const artifactTypeDisplay = computed(() => {
  if (props.type === 'code' && props.language) {
    return props.language.toUpperCase();
  }
  return props.type.charAt(0).toUpperCase() + props.type.slice(1);
});

// --- 交互逻辑 ---

const handleOpenArtifact = async () => {
  // 场景 1：内容已就绪（代码块内联内容），直接打开
  if (props.content) {
    contextOpenArtifact({
      type: props.type as any,
      content: props.content,
      title: props.title,
      language: props.language
    });
    return;
  }

  // 场景 2：内容为空但有 URL（文件型 Artifact），尝试 fetch 文本内容
  if (!props.content && props.url) {
    isLoading.value = true;
    try {
      const response = await fetch(props.url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const contentType = response.headers.get('content-type') || '';

      // 图片类型：直接把 URL 当作 content 传给面板（ArtifactEditor 支持图片 URL）
      if (contentType.startsWith('image/') || props.type === 'image') {
        contextOpenArtifact({
          type: 'image',
          content: props.url, // 图片用 URL 而非 base64
          title: props.title
        });
        return;
      }

      // PDF：浏览器无法跨域 fetch 二进制，改为新标签页打开
      if (contentType === 'application/pdf' || props.type === 'pdf') {
        window.open(props.url, '_blank', 'noopener,noreferrer');
        return;
      }

      // 文本类型（JSON/MD/HTML/纯文本）：尝试解析为文本
      const text = await response.text();
      contextOpenArtifact({
        type: props.type as any || 'markdown',
        content: text,
        title: props.title
      });
    } catch (err) {
      console.error('[ClaudeArtifactCard] Failed to fetch artifact content:', err);
      // fetch 失败时降级为直接下载
      window.open(props.url, '_blank', 'noopener,noreferrer');
    } finally {
      isLoading.value = false;
    }
    return;
  }

  // 兜底：内容为空也无 URL，尝试直接下载
  if (props.url) {
    window.open(props.url, '_blank', 'noopener,noreferrer');
  }
};
</script>