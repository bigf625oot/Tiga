<template>
  <div class="h-full overflow-y-auto p-4 custom-scrollbar">
    <div v-for="(group, groupName) in nodeGroups" :key="groupName" class="mb-6">
      <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">{{ groupName }}</h3>
      <div class="grid grid-cols-2 gap-3">
        <div 
          v-for="node in group" 
          :key="node.type"
          class="flex flex-col items-center justify-center p-3 rounded-lg border border-border bg-card hover:border-primary/50 hover:bg-accent/50 cursor-grab active:cursor-grabbing transition-all group"
          draggable="true"
          @dragstart="(event) => onDragStart(event, node)"
        >
          <div class="p-2 rounded-md bg-muted group-hover:bg-background transition-colors mb-2">
            <component :is="node.icon" class="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
          <span class="text-xs font-medium text-center truncate w-full">{{ node.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Play, 
  Square, 
  MessageSquare, 
  Database, 
  Cpu, 
  GitBranch, 
  Code, 
  Globe, 
  FileText,
  Bot,
  Users,
  ListOrdered,
  Split,
  Signpost
} from 'lucide-vue-next';

const nodeGroups = {
  '基础节点': [
    { type: 'start', label: '开始', icon: Play },
    { type: 'end', label: '结束', icon: Square },
  ],
  '逻辑处理': [
    { type: 'llm', label: '大模型', icon: Cpu },
    { type: 'steps', label: '步骤执行', icon: ListOrdered },
    { type: 'parallel', label: '并行执行', icon: Split },
    { type: 'condition', label: '条件分支', icon: GitBranch },
    { type: 'loop', label: '循环', icon: GitBranch }, // Icon reuse
    { type: 'router', label: '动态路由', icon: Signpost },
  ],
  '能力扩展': [
    { type: 'tool', label: '工具调用', icon: Globe },
    { type: 'code', label: '代码执行', icon: Code },
    { type: 'knowledge', label: '知识库', icon: Database },
  ],
  '交互组件': [
    { type: 'prompt', label: '提示词', icon: MessageSquare },
    { type: 'output', label: '输出', icon: FileText },
    { type: 'agent', label: '子智能体', icon: Bot },
    { type: 'team', label: '团队', icon: Users },
  ]
};

const onDragStart = (event: DragEvent, node: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify(node));
    event.dataTransfer.effectAllowed = 'move';
  }
};
</script>
