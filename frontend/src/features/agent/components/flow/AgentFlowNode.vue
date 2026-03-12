<template>
  <div 
    class="rounded-lg border shadow-sm transition-all duration-200 min-w-[140px] group relative"
    :class="[
      isSelected ? 'ring-2 ring-primary border-primary' : 'border-border hover:border-primary/50',
      statusClass
    ]"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <NodeToolbar
      :is-visible="isHovered || isSelected"
      :position="Position.Top"
      :offset="10"
      class="flex items-center gap-1 p-1 bg-background border rounded-md shadow-md z-50"
    >
      <button 
        class="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"
        title="复制节点"
        @click.stop="onCopy"
      >
        <Copy class="w-3.5 h-3.5" />
      </button>
      <button 
        class="p-1 hover:bg-red-100 rounded text-muted-foreground hover:text-red-600 transition-colors"
        title="删除节点"
        @click.stop="onDelete"
      >
        <Trash2 class="w-3.5 h-3.5" />
      </button>
    </NodeToolbar>

    <!-- Handle In -->
    <Handle 
      type="target" 
      :position="Position.Top" 
      class="!w-2 !h-2 !bg-muted-foreground hover:!bg-primary transition-colors !border-[1.5px] !border-background !-top-1" 
    />

    <div class="p-2 bg-card rounded-t-lg border-b border-border/50 flex items-center gap-2">
      <div 
        class="p-1 rounded-md shadow-sm shrink-0"
        :class="iconBgClass"
      >
        <component :is="icon" class="w-3 h-3 text-white" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="text-xs font-medium truncate">{{ data.label }}</div>
        <div class="text-[9px] text-muted-foreground truncate leading-none mt-0.5">{{ typeLabel }}</div>
      </div>
    </div>

    <div class="px-2 py-1.5 bg-card/50 rounded-b-lg text-[10px] text-muted-foreground min-h-[28px] flex items-center">
      <span v-if="data.description" class="line-clamp-2 leading-tight">{{ data.description }}</span>
      <span v-else class="italic opacity-50">未配置描述</span>
    </div>

    <!-- Handle Out -->
    <Handle 
      type="source" 
      :position="Position.Bottom" 
      class="!w-2 !h-2 !bg-muted-foreground hover:!bg-primary transition-colors !border-[1.5px] !border-background !-bottom-1" 
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Handle, Position, useVueFlow } from '@vue-flow/core';
import { NodeToolbar } from '@vue-flow/node-toolbar';
import { 
  Play, Square, MessageSquare, Database, Cpu, GitBranch, Code, Globe, FileText, Bot, HelpCircle, Users, ListOrdered, Split, Signpost,
  Trash2, Copy
} from 'lucide-vue-next';
import { useAgentFlowStore } from '../../store/agentFlow.store';

const props = defineProps<{
  id: string;
  data: any;
  selected?: boolean;
}>();

const { removeNodes } = useVueFlow();
const store = useAgentFlowStore();
const isSelected = computed(() => props.selected);
const isHovered = ref(false);

const onCopy = () => {
  // TODO: Implement copy logic
  console.log('Copy node:', props.id);
  // Example: store.copyNode(props.id);
};

const onDelete = () => {
  removeNodes(props.id);
  store.setSelectedNode(null);
};

const typeConfig: Record<string, { label: string; icon: any; color: string }> = {
  start: { label: '开始', icon: Play, color: 'bg-green-500' },
  end: { label: '结束', icon: Square, color: 'bg-red-500' },
  llm: { label: '大模型', icon: Cpu, color: 'bg-purple-500' },
  condition: { label: '条件分支', icon: GitBranch, color: 'bg-yellow-500' },
  loop: { label: '循环', icon: GitBranch, color: 'bg-orange-500' },
  steps: { label: '步骤执行', icon: ListOrdered, color: 'bg-teal-500' },
  parallel: { label: '并行执行', icon: Split, color: 'bg-violet-500' },
  router: { label: '动态路由', icon: Signpost, color: 'bg-fuchsia-500' },
  tool: { label: '工具调用', icon: Globe, color: 'bg-blue-500' },
  code: { label: '代码执行', icon: Code, color: 'bg-slate-700' },
  knowledge: { label: '知识库', icon: Database, color: 'bg-cyan-600' },
  prompt: { label: '提示词', icon: MessageSquare, color: 'bg-indigo-500' },
  output: { label: '输出', icon: FileText, color: 'bg-emerald-600' },
  agent: { label: '子智能体', icon: Bot, color: 'bg-pink-500' },
  team: { label: '团队', icon: Users, color: 'bg-rose-500' },
};

const typeInfo = computed(() => typeConfig[props.data.type] || { label: '未知节点', icon: HelpCircle, color: 'bg-gray-500' });
const icon = computed(() => typeInfo.value.icon);
const typeLabel = computed(() => typeInfo.value.label);
const iconBgClass = computed(() => typeInfo.value.color);

const statusClass = computed(() => {
  switch (props.data.status) {
    case 'running': return 'animate-pulse ring-2 ring-blue-400 border-blue-400';
    case 'success': return 'ring-2 ring-green-500 border-green-500';
    case 'error': return 'ring-2 ring-red-500 border-red-500';
    default: return '';
  }
});
</script>
