<template>
  <div class="h-full flex flex-col bg-background border-l border-border w-[350px]">
    <div class="p-4 border-b border-border flex items-center justify-between">
      <h3 class="font-medium">节点属性</h3>
      <Button variant="ghost" size="icon" @click="emit('close')">
        <X class="w-4 h-4" />
      </Button>
    </div>
    
    <div class="flex-1 overflow-y-auto p-4 space-y-4" v-if="selectedNode">
      <div class="space-y-2">
        <Label>节点名称</Label>
        <Input v-model="selectedNode.data.label" />
      </div>

      <div class="space-y-2">
        <Label>节点类型</Label>
        <div class="text-sm text-muted-foreground bg-muted p-2 rounded capitalize">
          {{ selectedNode.data.type }}
        </div>
      </div>

      <div class="space-y-2">
        <Label>描述</Label>
        <Textarea v-model="selectedNode.data.description" placeholder="输入节点描述..." />
      </div>
      
      <!-- Dynamic properties based on type -->
      <div class="border-t pt-4 mt-4">
        <h4 class="text-sm font-medium mb-3">配置参数</h4>
        
        <!-- LLM Node -->
        <template v-if="selectedNode.data.type === 'llm'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>模型选择</Label>
              <Select v-model="selectedNode.data.config.model">
                <SelectTrigger>
                  <SelectValue placeholder="选择模型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4">GPT-4</SelectItem>
                  <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                  <SelectItem value="claude-3">Claude 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1.5">
              <Label>系统提示词</Label>
              <Textarea v-model="selectedNode.data.config.systemPrompt" rows="4" placeholder="输入系统提示词..." />
            </div>
          </div>
        </template>
        
        <!-- Tool Node -->
        <template v-else-if="selectedNode.data.type === 'tool'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>工具选择</Label>
              <Select v-model="selectedNode.data.config.tool">
                <SelectTrigger>
                  <SelectValue placeholder="选择工具" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="search">网络搜索</SelectItem>
                  <SelectItem value="calculator">计算器</SelectItem>
                  <SelectItem value="weather">天气查询</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </template>

        <!-- Team Node -->
        <template v-else-if="selectedNode.data.type === 'team'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>团队名称</Label>
              <Input v-model="selectedNode.data.config.teamName" placeholder="输入团队名称..." />
            </div>
          </div>
        </template>

        <!-- Router Node -->
        <template v-else-if="selectedNode.data.type === 'router'">
          <div class="space-y-3">
            <div class="p-3 bg-muted rounded-md text-xs text-muted-foreground">
              动态路由节点：请在连接线上配置具体的分支条件（Case）。
            </div>
          </div>
        </template>

        <!-- Start Node -->
        <template v-else-if="selectedNode.data.type === 'start'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>输入变量定义 (JSON)</Label>
              <Textarea 
                v-model="selectedNode.data.config.inputSchema" 
                placeholder='{ "query": "string" }' 
                rows="5"
                class="font-mono text-xs"
              />
            </div>
          </div>
        </template>

        <!-- End Node -->
        <template v-else-if="selectedNode.data.type === 'end'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>输出模板</Label>
              <Textarea 
                v-model="selectedNode.data.config.outputTemplate" 
                placeholder="{{ result }}" 
                rows="3"
              />
            </div>
          </div>
        </template>

        <!-- Condition Node -->
        <template v-else-if="selectedNode.data.type === 'condition'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>判断条件 (Expression)</Label>
              <Input 
                v-model="selectedNode.data.config.expression" 
                placeholder="input.value > 0" 
                class="font-mono"
              />
              <p class="text-[10px] text-muted-foreground">使用 JavaScript 表达式，例如: input.score >= 60</p>
            </div>
          </div>
        </template>

        <!-- Loop Node -->
        <template v-else-if="selectedNode.data.type === 'loop'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>循环变量 (Item Variable)</Label>
              <Input v-model="selectedNode.data.config.itemVar" placeholder="item" />
            </div>
            <div class="space-y-1.5">
              <Label>最大循环次数</Label>
              <Input type="number" v-model="selectedNode.data.config.maxIterations" placeholder="10" />
            </div>
          </div>
        </template>
        
        <!-- Steps Node -->
        <template v-else-if="selectedNode.data.type === 'steps'">
           <div class="space-y-3">
            <div class="p-3 bg-muted rounded-md text-xs text-muted-foreground">
              步骤节点：请将子节点拖入此容器或按顺序连接子节点。
            </div>
          </div>
        </template>

        <!-- Parallel Node -->
        <template v-else-if="selectedNode.data.type === 'parallel'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>最大并发数</Label>
              <Input type="number" v-model="selectedNode.data.config.concurrency" placeholder="3" />
            </div>
          </div>
        </template>

        <!-- Code Node -->
        <template v-else-if="selectedNode.data.type === 'code'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>运行环境</Label>
              <Select v-model="selectedNode.data.config.runtime">
                <SelectTrigger>
                  <SelectValue placeholder="选择语言" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="python">Python 3.10</SelectItem>
                  <SelectItem value="nodejs">Node.js 18</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1.5">
              <Label>代码内容</Label>
              <Textarea 
                v-model="selectedNode.data.config.code" 
                placeholder="print('Hello World')" 
                rows="10"
                class="font-mono text-xs"
              />
            </div>
          </div>
        </template>

        <!-- Knowledge Node -->
        <template v-else-if="selectedNode.data.type === 'knowledge'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>知识库 ID</Label>
              <Input v-model="selectedNode.data.config.knowledgeBaseId" placeholder="kb_..." />
            </div>
            <div class="space-y-1.5">
              <Label>查询内容 (Query)</Label>
              <Textarea v-model="selectedNode.data.config.query" rows="2" placeholder="{{ input.query }}" />
            </div>
            <div class="space-y-1.5">
              <Label>召回数量 (Top K)</Label>
              <Input type="number" v-model="selectedNode.data.config.topK" placeholder="3" />
            </div>
          </div>
        </template>

        <!-- Prompt Node -->
        <template v-else-if="selectedNode.data.type === 'prompt'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>提示词模板</Label>
              <Textarea 
                v-model="selectedNode.data.config.template" 
                rows="6" 
                placeholder="你是一个助手，请回答用户的问题：{{ input.question }}" 
              />
            </div>
          </div>
        </template>

        <!-- Output Node -->
        <template v-else-if="selectedNode.data.type === 'output'">
          <div class="space-y-3">
             <div class="space-y-1.5">
              <Label>输出格式</Label>
              <Select v-model="selectedNode.data.config.format">
                <SelectTrigger>
                  <SelectValue placeholder="选择格式" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">纯文本</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1.5">
              <Label>输出内容</Label>
              <Textarea v-model="selectedNode.data.config.content" rows="4" placeholder="{{ result }}" />
            </div>
          </div>
        </template>

        <!-- Agent Node -->
        <template v-else-if="selectedNode.data.type === 'agent'">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <Label>智能体 ID</Label>
              <Input v-model="selectedNode.data.config.agentId" placeholder="agent_..." />
            </div>
            <div class="space-y-1.5">
              <Label>任务描述</Label>
              <Textarea v-model="selectedNode.data.config.task" rows="3" placeholder="请帮助我完成..." />
            </div>
          </div>
        </template>
        
        <div v-else class="text-sm text-muted-foreground text-center py-4 bg-muted/30 rounded-lg border border-dashed">
          暂无特定配置
        </div>
      </div>
    </div>
    
    <div v-else class="flex-1 flex items-center justify-center text-muted-foreground text-sm flex-col gap-2">
      <div class="p-3 bg-muted rounded-full">
        <X class="w-6 h-6 text-muted-foreground/50" />
      </div>
      请选择一个节点以编辑属性
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAgentFlowStore } from '../../store/agentFlow.store';
import { X } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const store = useAgentFlowStore();
const emit = defineEmits(['close']);

const selectedNode = computed(() => store.selectedNode);
</script>
