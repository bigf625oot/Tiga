<template>
  <div class="h-full flex flex-col bg-background animate-in fade-in duration-300 overflow-hidden font-sans text-foreground">
    <!-- 1. Header Container -->
    <header class="h-16 bg-background border-b border-border flex items-center justify-between px-6 shrink-0 z-20 shadow-sm">
        <div class="flex items-center gap-4 min-w-0">
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger as-child>
                        <Button variant="ghost" size="icon" @click="$emit('back')" class="text-muted-foreground hover:text-foreground">
                            <ArrowLeft class="w-5 h-5" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>返回</TooltipContent>
                </Tooltip>
            </TooltipProvider>
            
            <div class="flex flex-col min-w-0">
                <h1 class="text-lg font-semibold text-foreground leading-tight truncate max-w-md" :title="recording.filename">{{ recording.filename }}</h1>
                <div class="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                    <span>{{ formatDate(recording.created_at) }}</span>
                    <span class="w-0.5 h-0.5 rounded-full bg-slate-300"></span>
                    <span class="font-mono">{{ formatDuration(recording.duration) }}</span>
                    <span class="w-0.5 h-0.5 rounded-full bg-slate-300"></span>
                    <Badge 
                        :variant="getStatusVariant(recording.asr_status)" 
                        class="text-[10px] px-1.5 py-0 h-4 border-transparent"
                        :class="{ 
                            'bg-green-100 text-green-700 hover:bg-green-100/80': recording.asr_status === 'completed' 
                        }"
                    >
                        {{ getStatusText(recording.asr_status) }}
                    </Badge>
                </div>
            </div>
        </div>
        
        <div class="flex items-center gap-2">
            <Button size="sm" class="gap-2" @click="handleShare">
                <Share2 class="w-4 h-4" />
                分享
            </Button>
            
            <div class="h-6 w-px bg-border mx-1"></div>

            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger as-child>
                        <Button variant="ghost" size="icon" class="text-muted-foreground hover:text-foreground">
                            <FileText class="w-4 h-4" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>导出文档</TooltipContent>
                </Tooltip>

                <Tooltip>
                    <TooltipTrigger as-child>
                        <Button variant="ghost" size="icon" class="text-muted-foreground hover:text-foreground">
                            <Download class="w-4 h-4" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>下载音频</TooltipContent>
                </Tooltip>
                
                <Tooltip>
                    <TooltipTrigger as-child>
                        <Button variant="ghost" size="icon" class="text-muted-foreground hover:text-destructive hover:bg-destructive/10">
                            <Trash2 class="w-4 h-4" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>删除录音</TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    </header>

    <!-- 2. Main Content Container -->
    <main class="flex-1 flex flex-col min-h-0 relative bg-muted/10">
        <!-- Player Section -->
        <div class="border-b border-border bg-background">
            <WaveformPlayer 
                :src="recording.play_url" 
                :seekTime="seekTime"
                @timeupdate="onTimeUpdate"
            />
        </div>

        <!-- Content Tabs -->
        <Tabs v-model="activeKey" class="flex-1 flex flex-col min-h-0" :default-value="activeKey">
            <!-- Tabs Header -->
            <div class="flex items-center justify-between px-6 border-b border-border bg-background shrink-0">
                <TabsList class="h-12 bg-transparent p-0 w-auto justify-start rounded-none border-b-0">
                    <TabsTrigger 
                        value="transcript" 
                        class="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 font-medium transition-none"
                    >
                        全文转写
                    </TabsTrigger>
                    <TabsTrigger 
                        value="summary"
                        class="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 font-medium transition-none"
                    >
                        智能摘要
                    </TabsTrigger>
                    <TabsTrigger 
                        value="recommendation"
                        class="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 font-medium transition-none"
                    >
                        内容推荐
                    </TabsTrigger>
                </TabsList>

                <!-- Right Controls -->
                <div class="flex items-center gap-4">
                    <!-- Font Size Controls -->
                    <div class="flex items-center bg-muted rounded-md p-0.5">
                        <Button variant="ghost" size="sm" class="h-6 w-8 text-xs p-0" @click="adjustFontSize(-2)" title="减小字号">A-</Button>
                        <span class="text-[10px] text-muted-foreground px-1 select-none w-6 text-center">{{ fontSize }}</span>
                        <Button variant="ghost" size="sm" class="h-6 w-8 text-xs p-0" @click="adjustFontSize(2)" title="增大字号">A+</Button>
                    </div>

                    <div v-if="activeKey === 'transcript'" class="flex items-center gap-2 border-l border-border pl-4">
                        <template v-if="isEditing">
                            <Button variant="ghost" size="sm" class="h-8 text-xs" @click="isEditing = false">
                                取消
                            </Button>
                            <Button size="sm" class="h-8 text-xs gap-1" @click="saveTranscript">
                                <Save class="w-3.5 h-3.5" />
                                保存
                            </Button>
                        </template>
                        <Button v-else variant="ghost" size="sm" class="h-8 text-xs text-primary hover:text-primary/80 gap-1" @click="toggleEditMode">
                            <Edit3 class="w-3.5 h-3.5" />
                            编辑模式
                        </Button>
                    </div>
                </div>
            </div>

            <!-- Tabs Content -->
            <div class="flex-1 min-h-0 bg-background">
                <TabsContent value="transcript" class="h-full m-0 data-[state=active]:flex flex-col ring-0 outline-none">
                    <ScrollArea class="h-full w-full">
                        <div class="p-6 max-w-4xl mx-auto">
                            <div v-if="isAsrLoading" class="space-y-4 animate-pulse w-full">
                                <div class="h-4 bg-muted rounded w-3/4"></div>
                                <div class="h-4 bg-muted rounded w-full"></div>
                                <div class="h-4 bg-muted rounded w-5/6"></div>
                                <div class="h-4 bg-muted rounded w-4/5"></div>
                            </div>
                            <div v-else class="w-full">
                                <textarea 
                                    v-if="isEditing"
                                    v-model="editContent"
                                    class="w-full min-h-[500px] p-0 border-0 outline-none bg-transparent resize-none leading-relaxed font-sans focus:ring-0"
                                    :style="{ fontSize: fontSize + 'px' }"
                                    placeholder="输入转写内容..."
                                ></textarea>
                                <div 
                                    v-else
                                    class="prose prose-slate max-w-none text-slate-700 leading-loose whitespace-pre-wrap font-sans text-left"
                                    :style="{ fontSize: fontSize + 'px' }"
                                >
                                    <template v-if="transcriptionData && transcriptionData.length > 0">
                                        <span 
                                            v-for="(sentence, index) in transcriptionData" 
                                            :key="index"
                                            class="cursor-pointer hover:bg-primary/10 transition-colors rounded px-0.5 py-0.5"
                                            :class="{ 'bg-primary/20 text-primary font-medium': isCurrentSentence(sentence) }"
                                            @click="handleSentenceClick(sentence)"
                                            :title="formatTime(sentence.BeginTime/1000)"
                                        >{{ sentence.Text }}</span>
                                    </template>
                                    <template v-else>
                                        {{ recording.transcription_text || '暂无转写内容' }}
                                    </template>
                                </div>
                            </div>
                        </div>
                    </ScrollArea>
                </TabsContent>

                <TabsContent value="summary" class="h-full m-0 data-[state=active]:flex flex-col ring-0 outline-none">
                    <ScrollArea class="h-full w-full">
                         <div class="p-6 max-w-4xl mx-auto">
                            <div v-if="isSummaryLoading" class="space-y-4 animate-pulse w-full">
                                <div class="h-32 bg-muted rounded-lg"></div>
                            </div>
                            <div v-else class="w-full">
                                <div class="markdown-body text-slate-700 leading-relaxed text-left" 
                                    :style="{ fontSize: fontSize + 'px' }"
                                    v-html="renderMarkdown(recording.summary_text)"></div>
                            </div>
                        </div>
                    </ScrollArea>
                </TabsContent>
                
                <TabsContent value="recommendation" class="h-full m-0 data-[state=active]:flex flex-col ring-0 outline-none">
                    <ScrollArea class="h-full w-full">
                        <div class="p-6 max-w-6xl mx-auto">
                            <div v-if="isRecommendationLoading" class="w-full">
                                <div class="h-4 w-32 bg-muted rounded mb-4 animate-pulse"></div>
                                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                    <div v-for="i in 8" :key="i" class="flex items-center gap-2 p-3 border border-border rounded-lg animate-pulse bg-muted/10">
                                        <div class="w-8 h-8 rounded bg-muted shrink-0"></div>
                                        <div class="flex-1 min-w-0 space-y-2">
                                            <div class="h-3 bg-muted rounded w-3/4"></div>
                                            <div class="h-2 bg-muted rounded w-1/4"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="w-full">
                                <div class="space-y-8">
                                    <div v-if="relatedDocs.length > 0">
                                        <h4 class="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wide">相关知识库文档</h4>
                                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                            <div 
                                                v-for="(doc, idx) in relatedDocs" 
                                                :key="idx"
                                                class="group flex items-center gap-3 p-3 bg-card border border-border rounded-lg hover:border-primary/50 hover:shadow-md transition-all cursor-pointer relative overflow-hidden"
                                                @click="handleDocClick(doc)"
                                            >
                                                <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 text-primary">
                                                    <FileText class="w-4 h-4" />
                                                </div>
                                                
                                                <div class="flex-1 min-w-0 flex flex-col gap-0.5">
                                                    <h5 class="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors" :title="doc.title">{{ doc.title }}</h5>
                                                    <div class="flex items-center gap-2">
                                                        <Badge variant="secondary" class="text-[10px] px-1 py-0 h-4 rounded-sm font-normal">{{ doc.type || 'DOC' }}</Badge>
                                                    </div>
                                                </div>
                                                
                                                <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute right-2 top-1/2 -translate-y-1/2">
                                                    <ExternalLink class="w-4 h-4 text-primary" />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="flex flex-col items-center justify-center py-20 text-muted-foreground">
                                        <div class="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mb-4">
                                            <File class="w-10 h-10 text-muted-foreground/50" />
                                        </div>
                                        <p class="text-sm font-medium">暂无相关推荐内容</p>
                                        <p class="text-xs text-muted-foreground mt-1">系统未找到与此录音相关的知识库文档</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </ScrollArea>
                </TabsContent>
            </div>
        </Tabs>
    </main>

    <!-- Share Dialog -->
    <Dialog v-model:open="shareModalVisible">
        <DialogContent class="sm:max-w-md">
            <DialogHeader>
                <DialogTitle>分享录音</DialogTitle>
                <DialogDescription>
                    创建一个链接以分享此录音给其他人。
                </DialogDescription>
            </DialogHeader>
            <div class="py-4 space-y-4">
                <div class="space-y-2">
                    <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">链接权限</label>
                    <Select v-model="sharePermission">
                        <SelectTrigger>
                            <SelectValue placeholder="选择权限" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="view">仅查看</SelectItem>
                            <SelectItem value="comment">允许评论</SelectItem>
                            <SelectItem value="edit">允许编辑</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="grid flex-1 gap-2">
                        <div class="flex items-center justify-between bg-muted p-3 rounded-md border border-border">
                            <span class="text-sm text-muted-foreground truncate">{{ shareLink }}</span>
                        </div>
                    </div>
                    <Button size="sm" class="px-3" @click="handleShareConfirm">
                        <span class="sr-only">复制</span>
                        <Share2 class="h-4 w-4" />
                    </Button>
                </div>
                <div class="flex items-center justify-between">
                     <div class="flex items-center space-x-2">
                        <Switch id="allow-comments" v-model:checked="allowComments" />
                        <label
                            for="allow-comments"
                            class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                            允许评论
                        </label>
                     </div>
                </div>
            </div>
            <DialogFooter class="sm:justify-start">
                <Button type="button" variant="secondary" @click="shareModalVisible = false">
                    关闭
                </Button>
                <Button type="button" @click="handleShareConfirm">
                    复制链接
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import { marked } from 'marked';
import { 
  ArrowLeft, Share2, Download, Trash2, FileText, 
  Edit3, Save, X, File, FileType, ExternalLink 
} from 'lucide-vue-next';
import WaveformPlayer from './WaveformPlayer.vue';

// Shadcn Components
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger
} from '@/components/ui/tooltip';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/toast/use-toast';

const { toast } = useToast();

const props = defineProps({
    recording: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['back']);

const api = axios.create({
    baseURL: '/api/v1' 
});

const activeKey = ref('transcript');
const isEditing = ref(false);
const editContent = ref('');
const shareModalVisible = ref(false);
const sharePermission = ref('comment');
const allowComments = ref(true);
const shareLink = ref('https://tiga.app/share/' + props.recording.id);
const fontSize = ref(14);
const currentTime = ref(0);
const seekTime = ref(undefined);

const isAsrLoading = computed(() => ['processing', 'pending'].includes(props.recording.asr_status));
const isSummaryLoading = computed(() => ['processing', 'pending'].includes(props.recording.summary_status));
const isRecommendationLoading = computed(() => ['processing', 'pending'].includes(props.recording.recommendation_status));

const relatedDocs = computed(() => {
    try {
        const text = props.recording.recommendation_text;
        if (!text) return [];
        
        if (text.trim().startsWith('[')) {
            const parsed = JSON.parse(text);
            return parsed.map(item => ({
                ...item,
                type: getFileType(item.title || item.file_path),
                title: item.title || '无标题文档'
            }));
        }
        return [];
    } catch (e) {
        console.error("Failed to parse recommendation_text", e);
        return [];
    }
});

// Mock transcription data for demo if not present (in real app this comes from recording)
const transcriptionData = computed(() => {
    try {
        if (props.recording.transcription_json) {
             return JSON.parse(props.recording.transcription_json);
        }
    } catch(e) {}
    return []; 
});

const isCurrentSentence = (sentence) => {
    return currentTime.value * 1000 >= sentence.BeginTime && currentTime.value * 1000 < sentence.EndTime;
};

const handleSentenceClick = (sentence) => {
    seekTime.value = sentence.BeginTime / 1000;
};

const getFileType = (filename) => {
    if (!filename) return 'DOC';
    const ext = filename.split('.').pop().toLowerCase();
    if (['pdf'].includes(ext)) return 'PDF';
    if (['doc', 'docx'].includes(ext)) return 'DOC';
    if (['ppt', 'pptx'].includes(ext)) return 'PPT';
    if (['xls', 'xlsx', 'csv'].includes(ext)) return 'XLS';
    if (['md', 'txt'].includes(ext)) return 'TXT';
    return 'FILE';
};

const handleDocClick = (doc) => {
    toast({ description: `打开文档: ${doc.title}` });
};

const toggleEditMode = () => {
    if (isEditing.value) {
        isEditing.value = false;
        editContent.value = '';
    } else {
        editContent.value = props.recording.transcription_text || '';
        isEditing.value = true;
    }
};

const saveTranscript = async () => {
    try {
        props.recording.transcription_text = editContent.value;
        isEditing.value = false;
        
        await api.patch(`/recordings/${props.recording.id}`, {
            transcription_text: editContent.value
        });
        toast({ title: "已保存", description: "转写内容已更新" });
    } catch (e) {
        console.error(e);
        toast({ variant: "destructive", title: "保存失败", description: "请稍后重试" });
    }
};

const renderMarkdown = (text) => {
    try {
        return marked.parse(text || '');
    } catch (e) {
        return text;
    }
};

const onTimeUpdate = (time) => {
    currentTime.value = time;
};

const handleShare = () => {
    shareModalVisible.value = true;
};

const handleShareConfirm = () => {
    navigator.clipboard.writeText(shareLink.value);
    toast({ title: "链接已复制", description: "分享链接已复制到剪贴板" });
    shareModalVisible.value = false;
};

const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD HH:mm');
};

const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
};

const formatDuration = (ms) => {
    const durationSec = Math.floor(ms / 1000);
    const min = Math.floor(durationSec / 60);
    const sec = durationSec % 60;
    return (min > 0 ? min + ":" : "0:") + (sec < 10 ? "0" + sec : sec);
};

const getStatusVariant = (status) => {
    switch(status) {
        case 'completed': return 'outline'; 
        case 'processing': return 'secondary';
        case 'failed': return 'destructive';
        default: return 'outline';
    }
};

const getStatusText = (status) => {
    switch(status) {
        case 'completed': return '已完成';
        case 'processing': return '转写中';
        case 'failed': return '失败';
        default: return '待处理';
    }
};

const adjustFontSize = (delta) => {
    const newSize = fontSize.value + delta;
    if (newSize >= 12 && newSize <= 24) {
        fontSize.value = newSize;
    }
};
</script>

<style scoped>
/* Markdown Styles */
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) {
    font-weight: 600;
    margin-bottom: 0.5em;
    margin-top: 1em;
    color: inherit;
}
.markdown-body :deep(ul), .markdown-body :deep(ol) {
    padding-left: 1.5em;
    margin-bottom: 1em;
    list-style-type: disc;
}
.markdown-body :deep(li) {
    margin-bottom: 0.25em;
}
.markdown-body :deep(p) {
    margin-bottom: 1em;
}
</style>