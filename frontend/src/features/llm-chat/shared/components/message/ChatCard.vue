<template>
  <div 
    class="flex w-full mb-4 group chat-card" 
    :class="[
      isUser ? 'flex-row-reverse' : 'flex-row',
      !showAvatar ? (isUser ? 'mr-10' : 'ml-10') : ''
    ]"
  >
    <!-- Avatar -->
    <div 
      v-if="showAvatar" 
      class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 overflow-hidden mt-1 transition-all duration-300 hover:scale-105 bg-background"
      :class="isUser ? 'ml-3' : 'mr-3'"
    >
      <img :src="avatarSrc" :alt="avatarAlt" class="w-full h-full object-cover p-0.5" />
    </div>

    <!-- Message Content Wrapper -->
    <div 
      class="flex flex-col flex-1 min-w-0" 
      :class="[isUser ? 'items-end' : 'items-start']"
    >
      <!-- Sender Name & Time (Agent) -->
      <div v-if="!isUser" class="flex items-center gap-2 mb-1 px-1">
        <span class="text-sm font-medium text-foreground/80">{{ agent?.name || 'Tiga' }}</span>
        <span class="text-xs text-muted-foreground/40">{{ formatTime(message.timestamp) }}</span>
        <span v-if="message.meta_data?.duration" class="text-xs text-muted-foreground/40">耗时 {{ formatDuration(message.meta_data.duration) }}</span>
      </div>

      <!-- Sender Name & Time (User - Optional, usually hidden or on right) -->
      <div v-if="isUser && showMeta" class="flex items-center gap-2 mb-2 px-1 text-xs text-muted-foreground">
         <span>{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Bubble -->
      <div 
        class="relative text-sm leading-normal transition-all duration-200 min-w-0"
        :class="[bubbleClasses, isUser ? 'max-w-[85%] w-fit' : 'mt-1 w-full']"
      >
        <template v-if="isUser">
            <div v-if="isEditing" class="flex flex-col gap-2 min-w-[200px]">
                <textarea
                    v-model="editContent"
                    class="w-full bg-transparent text-primary-foreground placeholder:text-primary-foreground/50 resize-none outline-none border border-primary-foreground/20 rounded p-2 focus:border-primary-foreground/50 transition-colors custom-scrollbar"
                    rows="3"
                    @keydown.ctrl.enter="saveEdit"
                    @keydown.esc="cancelEdit"
                ></textarea>
                <div class="flex justify-end gap-2 text-xs">
                    <button @click="cancelEdit" class="px-2 py-1 rounded bg-primary-foreground/10 hover:bg-primary-foreground/20 transition-colors">取消</button>
                    <button @click="saveEdit" class="px-2 py-1 rounded bg-primary-foreground text-primary hover:bg-primary-foreground/90 transition-colors">发送</button>
                </div>
            </div>
            <div v-else class="flex flex-col gap-2">
                <MarkdownRenderer 
                    v-if="contentRef" 
                    :content="contentRef" 
                    proseClass="prose prose-sm max-w-none text-white prose-p:text-white prose-headings:text-white prose-strong:text-white prose-em:text-white prose-a:text-white prose-li:text-white prose-blockquote:text-white/80 prose-blockquote:border-white/30 prose-code:text-white prose-code:bg-white/10" 
                />
                <template v-if="userImageAttachments.length > 0">
                    <div v-for="(img, idx) in userImageAttachments" :key="'img-' + idx" class="user-image-list flex flex-wrap gap-2">
                        <img
                            :src="img.url"
                            :alt="img.alt || 'image'"
                            class="max-w-[200px] max-h-[200px] rounded-lg object-cover cursor-pointer hover:opacity-90 transition-opacity"
                            @click="openUrl(img.url)"
                        />
                    </div>
                </template>
                <template v-if="userFileAttachments.length > 0">
                    <div v-for="(file, idx) in userFileAttachments" :key="'file-' + idx" class="user-file-item flex items-center gap-2 text-sm">
                        <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-foreground/10 text-primary-foreground">
                            <span class="font-medium">{{ file.name }}</span>
                            <span v-if="file.size" class="text-xs opacity-70">{{ file.size }}</span>
                        </div>
                    </div>
                </template>
            </div>
        </template>

        <!-- Agent Mode: Rich Content -->
        <div v-else class="agent-content flex flex-col gap-2 min-w-0 w-full max-w-full">
            <div v-if="isStreaming && isLast && !message.content && !message.reasoning && (!message.steps || message.steps.length === 0) && (!message.tools || message.tools.length === 0)" class="flex items-center gap-2 py-1">
                <span class="relative flex h-2.5 w-2.5">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                </span>
                <span class="text-xs text-muted-foreground/60 font-medium animate-pulse">正在生成回复...</span>
            </div>
            
            <MessageRenderer 
                v-else-if="adaptedMessage && adaptedMessage.blocks && adaptedMessage.blocks.length > 0"
                :message="adaptedMessage" 
                @locate-node="$emit('locate-node', $event)"
                @open-doc-space="$emit('open-doc-space', $event)"
                @resend-message="$emit('resend-message', message)"
                class="w-full flex-1"
            />
            
            <!-- Fallback: 只在没有blocks也没有content时才显示 -->
            <div v-else-if="!message.content && !message.reasoning" class="text-muted-foreground italic text-sm py-2">
              (无返回内容)
            </div>
        </div>
      </div>

      <!-- Actions (Outside Bubble) -->
      <div 
        class="flex items-center gap-1.5 mt-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-1 group-hover:translate-y-0" 
        :class="isUser ? 'mr-1 justify-end' : 'ml-1'"
      >
          <template v-if="isUser">
              <button v-if="!isEditing" class="p-1 text-muted-foreground/40 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-all" title="编辑" @click="startEdit">
                  <Pencil class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/40 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-all" title="复制" @click="copyText(message.content)">
                  <Copy class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/40 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-all" title="重新发送" @click="$emit('resend-message', message)">
                  <RotateCcw class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/40 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-all" title="删除" @click="$emit('delete-message', message)">
                  <Trash2 class="w-3.5 h-3.5" />
              </button>
          </template>
          <template v-else>
              <button class="p-1 text-muted-foreground/40 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-all" title="复制" @click="copyText(message.content)">
                  <Copy class="w-3.5 h-3.5" />
              </button>
              <button class="p-1 text-muted-foreground/40 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-all" title="引用" @click="$emit('quote-message', message.content)">
                  <Quote class="w-3.5 h-3.5" />
              </button>
              <button
                  class="p-1 text-muted-foreground/40 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded transition-all relative"
                  title="摘录到秒记"
                  @click="handleExcerpt"
              >
                  <Bookmark class="w-3.5 h-3.5" :class="{'fill-current text-amber-500 animate-pulse': isExcerptionAnimating}" />
              </button>
              <div class="w-px h-3 bg-border/40 mx-0.5"></div>
              <button 
    class="p-1 rounded transition-all" 
    :class="message.feedback?.rating === 'like' ? 'text-green-600 bg-green-50 dark:bg-green-900/20' : 'text-muted-foreground/40 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'"
    title="赞"
    @click="$emit('feedback', message, 'like')"
>
    <ThumbsUp class="w-3.5 h-3.5" :class="{'fill-current': message.feedback?.rating === 'like'}" />
</button>
<button 
    class="p-1 rounded transition-all" 
    :class="message.feedback?.rating === 'dislike' ? 'text-red-600 bg-red-50 dark:bg-red-900/20' : 'text-muted-foreground/40 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'"
    title="踩"
    @click="$emit('feedback', message, 'dislike')"
>
    <ThumbsDown class="w-3.5 h-3.5" :class="{'fill-current': message.feedback?.rating === 'dislike'}" />
</button>
          </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import dayjs from 'dayjs';
import { Copy, ThumbsUp, ThumbsDown, Quote, Bookmark, Brain, ChevronRight, Trash2, Pencil, RotateCcw } from 'lucide-vue-next';
import { formatTime, formatDuration } from '@/features/llm-chat/shared/utils/qa/dateUtils';
import type { Message } from '@/features/llm-chat/shared/types';

// 新引入的 UI 组件
import MessageRenderer from './MessageRenderer.vue';
import MarkdownRenderer from '@/features/llm-chat/shared/components/common/MarkdownRenderer.vue';
import { adaptMessageToBlocks } from '@/features/llm-chat/shared/utils/MessageAdapter';

const props = withDefaults(defineProps<{
  message: Message;
  type?: string;
  isUser?: boolean;
  showAvatar?: boolean;
  showMeta?: boolean;
  agent?: Record<string, any> | null;
  isLast?: boolean;
  isStreaming?: boolean;
  currentModeId?: string | null;
}>(), {
  type: 'knowledge_qa',
  isUser: false,
  showAvatar: true,
  showMeta: false,
  agent: null,
  isLast: false,
  isStreaming: false,
  currentModeId: null,
});

const emit = defineEmits(['locate-node', 'open-doc-space', 'quote-message', 'excerpt-message', 'delete-message', 'resend-message', 'edit-message', 'feedback']);

const isExcerptionAnimating = ref(false);
const isStepsExpanded = ref(true);

const isEditing = ref(false);
const editContent = ref('');

const startEdit = () => {
    editContent.value = props.message.content;
    isEditing.value = true;
};

const cancelEdit = () => {
    isEditing.value = false;
    editContent.value = '';
};

const saveEdit = () => {
    if (!editContent.value.trim()) return;
    emit('edit-message', { originalMessage: props.message, newContent: editContent.value });
    isEditing.value = false;
};

const handleExcerpt = () => {
    isExcerptionAnimating.value = true;
    emit('excerpt-message', props.message.content);
    setTimeout(() => {
        isExcerptionAnimating.value = false;
    }, 600);
};

// Composables
const contentRef = computed(() => props.message?.content || '');

const adaptedMessage = computed(() => {
    const adapted = adaptMessageToBlocks(props.message, props.isStreaming, props.isLast, props.currentModeId ?? undefined);
    // 确保永远返回一个有效的 ChatMessage 对象，防止 undefined 导致组件卸载
    return adapted || { id: String(Date.now()), role: 'assistant', status: 'completed', blocks: [] };
});

const userImageAttachments = computed(() => {
    if (!props.isUser) return [];
    const images: { url: string; alt: string }[] = [];
    const msg = props.message;

    if (msg.artifacts && Array.isArray(msg.artifacts)) {
        for (const a of msg.artifacts as any[]) {
            if (a?.url && (a.type === 'image' || a.media_kind === 'image' || /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(a.name || ''))) {
                images.push({ url: a.url, alt: a.name || 'image' });
            }
        }
    }

    if (msg.images && Array.isArray(msg.images)) {
        for (const img of msg.images as any[]) {
            const url = img.url || img.oss_url || img.id || '';
            if (url) {
                images.push({ url, alt: img.name || img.alt || 'image' });
            }
        }
    }

    return images;
});

const userFileAttachments = computed(() => {
    if (!props.isUser) return [];
    const files: { name: string; url: string; size?: string }[] = [];
    const msg = props.message;

    if (msg.artifacts && Array.isArray(msg.artifacts)) {
        for (const a of msg.artifacts as any[]) {
            if (a?.url && !(a.type === 'image' || a.media_kind === 'image' || /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(a.name || ''))) {
                files.push({
                    name: a.name || 'file',
                    url: a.url,
                    size: a.size ? `${(a.size / 1024).toFixed(1)} KB` : undefined
                });
            }
        }
    }

    return files;
});

watch(() => props.message.steps, (newVal, oldVal) => {
    if (newVal && newVal.length > 0 && (!oldVal || oldVal.length === 0)) {
        isStepsExpanded.value = true;
    }
}, { deep: true });

const bubbleClasses = computed(() => {
  if (props.isUser) {
    return 'bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm';
  } else {
    // 采用与 ChatView demo 完全一致的全宽块级布局
    return 'bg-transparent text-foreground px-0 py-0 w-full';
  }
});

const avatarSrc = computed(() => {
  if (props.isUser) return '/user/hair.svg';
  return props.agent?.icon || props.agent?.icon_url || '/tiga.svg';
});
const avatarAlt = computed(() => (props.isUser ? 'user' : 'agent'));

// Methods
const copyText = (text: string) => navigator.clipboard.writeText(text || '');

const openUrl = (url: string) => {
    if (url && typeof window !== 'undefined') {
        window.open(url, '_blank');
    }
};
</script>

