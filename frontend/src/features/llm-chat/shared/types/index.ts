export type StreamStatus = 'streaming' | 'completed' | 'error';

export type BlockType = 
  | 'thought' 
  | 'text' 
  | 'tool_call' 
  | 'tool_result' 
  | 'action' 
  | 'plan' 
  | 'terminal' 
  | 'search' 
  | 'visualization' 
  | 'confirmation'
  | 'sandbox'
  | 'kb_retrieval'
  | 'media'
  | 'image';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  status: StreamStatus;
  blocks: ContentBlock[]; // 鏈夊簭鍧楁暟缁?
}

export interface ThoughtBlock {
  type: 'thought';
  content: string;
  state: 'thinking' | 'collapsed' | 'expanded';
}

export interface PlanStep {
  id: string;
  text: string;
  status: 'pending' | 'running' | 'completed' | 'error';
}

export interface PlanBlock {
  type: 'plan';
  steps: PlanStep[];
}


export interface TextBlock {
  type: 'text';
  content: string;
}

export interface ToolCallBlock {
  type: 'tool_call';
  call_id: string;
  tool_name: string;
  arguments: object | string;
  raw_arguments?: string; // 尚未完成 JSON 解析的流式增量字符串
  state: 'streaming' | 'running' | 'success' | 'error';
}

export interface ToolResultBlock {
  type: 'tool_result';
  call_id: string;
  content: string;
  is_error: boolean;
}

export interface TerminalBlock {
  type: 'terminal';
  command: string;
  output: string;
  status: 'running' | 'success' | 'error';
}

export interface ActionBlock {
  type: 'action';
  action_type: 'create_file' | 'edit_file' | 'delete_file';
  path: string;
  description: string;
  diff: string; // Unified Diff 鏍煎紡
  status: 'pending' | 'applied' | 'rejected';
}

export interface SearchSource {
  title: string;
  url: string;
  favicon?: string;
  snippet?: string;
  index?: number;
  publish_date?: string;
}

export interface SearchBlock {
  type: 'search';
  query: string;
  sources: SearchSource[];
}

export interface ConfirmationBlock {
  type: 'confirmation';
  message: string;
  context_id: string;
  action_id?: string;
  status?: 'pending' | 'approved' | 'denied' | 'expired';
}

export interface VisualizationBlock {
  type: 'visualization';
  vis_type: 'mermaid' | 'markmap' | 'recharts' | 'echarts' | 'dynamic_chart' | 'd3' | 'antv';
  data: string | any;
}

export interface ImageBlock {
  type: 'image';
  source_type: 'url' | 'base64' | 'upload';
  url?: string;
  base64?: string;
  alt?: string;
  width?: number;
  height?: number;
}

export interface MediaBlock {
  type: 'media';
  media_type: 'audio' | 'video';
  url: string;
  name?: string;
  cover_url?: string;
  duration?: number;
}

export interface ResourceBlock {
  type: 'resource';
  resource_type: 'doc' | 'file';
  data: any;
}

export interface ErrorBlock {
  type: 'error';
  message: string;
  can_retry: boolean;
}

export interface SandboxBlock {
  type: 'sandbox';
  status: 'pending' | 'running' | 'success' | 'error';
  code: string;
  output?: string;
}

export interface KbRetrievalBlock {
  type: 'kb_retrieval';
  query: string;
  status: 'searching' | 'completed';
  results: any[];
}

export interface ReferencesBlock {
  type: 'references';
  sources: any[];
}

export interface SoloLayoutBlock {
  type: 'solo_layout';
  original_message: any; // Temporarily passing original message to reuse SoloTaskCard component logic, or fully map it
  is_last: boolean;
  is_streaming: boolean;
}

export type ContentBlock = 
  | ThoughtBlock
  | TextBlock
  | ToolCallBlock
  | ToolResultBlock
  | PlanBlock
  | TerminalBlock
  | ActionBlock
  | SearchBlock
  | ConfirmationBlock
  | VisualizationBlock
  | MediaBlock
  | ImageBlock
  | ResourceBlock
  | ErrorBlock
  | SandboxBlock
  | KbRetrievalBlock
  | ReferencesBlock
  | SoloLayoutBlock;

export type Role = 'user' | 'assistant' | 'system';

export type MessageStatus = 'sending' | 'sent' | 'error' | 'success';

export interface MessageSource {
  title: string;
  docId?: string;
  chunkId?: string;
  nodeId?: string;
  snippet?: string;
  index?: number;
  publish_date?: string;
  [key: string]: any;
}

export interface MessageMetadata {
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  latency_ms?: number;
  finish_reason?: 'stop' | 'length' | 'tool_calls' | 'content_filter' | 'error';
  [key: string]: any;
}

export interface MessageFeedback {
  rating: 'like' | 'dislike';
  tags?: string[];
  comment?: string;
}

export interface ChartConfig {
  type: string;
  data: any;
  options?: any;
  _type?: string; // Optional metadata for chart library type (e.g. d3, antv, echarts)
}

export interface StreamEventItem {
  id: string;
  event: string;
  content: string;
  ts: number;
  raw?: any;
}

export interface Message {
  role: Role;
  content: string;
  timestamp?: string | number;
  type?: string;
  status?: MessageStatus;
  reasoning?: string;
  steps?: { content: string; step: number }[];
  stream_events?: StreamEventItem[];
  chart_config?: ChartConfig;
  sources?: MessageSource[];
  isSystem?: boolean;
  parent_id?: string;
  version?: number;
  is_truncated?: boolean;
  metadata?: MessageMetadata;
  feedback?: MessageFeedback;
  [key: string]: any;
}

export interface MessageGroup {
  role: Role;
  messages: Message[];
  timestamp: any;
  lastTimestamp: any;
  showTime: boolean;
}

export interface Agent {
  id: string;
  name: string;
  icon?: string;
  icon_url?: string;
  description?: string;
  category?: string;
  provider?: string;
  model_id?: string;
  system_prompt?: string;
  instructions?: string[];
  enable_react?: boolean;
  enable_cot?: boolean;
  show_tool_calls?: boolean;
  enable_markdown?: boolean;
  role?: string;
  is_template?: boolean;
  model_config?: Record<string, any>;
  tools_config?: any[];
  mcp_config?: any[];
  skills_config?: Record<string, any>;
  knowledge_config?: Record<string, any>;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  members?: Agent[];
}

export type ModeType = 'auto' | 'chat' | 'quick' | 'solo' | 'team' | 'workflow' | 'auto_task';

export interface Session {
  id: string;
  title: string;
  agent_id?: string;
  mode?: ModeType;
  messages: Message[];
  workflow_state?: any;
  created_at?: string;
  updated_at?: string;
}

export interface UserScript {
  id: string;
  title: string;
  content: string;
  agent_id?: string;
}

export interface Attachment {
  type: 'local' | 'knowledge';
  name: string;
  size: number;
  file?: File | null; // For local files
  id?: string; // For knowledge docs
  status?: 'uploading' | 'parsing' | 'success' | 'error';
  progress?: number; // 0-100
  summary?: string; // Document summary after parsing
  pageCount?: number;
  wordCount?: number;
  errorMessage?: string;
}

export interface KnowledgeDoc {
  id: string;
  filename: string;
  file_size: number;
  created_at?: string;
  updated_at: string;
}


export type AgentEventType =
  | 'thought'
  | 'plan_created'
  | 'task_start'
  | 'tool_call'
  | 'call'
  | 'tool_output'
  | 'result'
  | 'artifact'
  | 'summary';

export type AgentTaskStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AgentTaskStep {
  id: string;
  title: string;
  status: AgentTaskStatus;
  description: string;
  assigned_role: string;
}

export interface AgentExecutionPlan {
  plan_id: string;
  reasoning: string;
  tasks: AgentTaskStep[];
}

export interface AgentToolCallInfo {
  tool: string;
  args: Record<string, any>;
  task_id?: string;
}

// tool_output 浜嬩欢鍐呭
export interface AgentObservationInfo {
  tool: string;
  output: any;
  logs: string[];
  is_error: boolean;
  task_id?: string;
}

export interface AgentArtifactCard {
  file_name: string;
  file_size: number;
  url: string;
  type: string;
}

// 
export interface AgentTaskStartInfo {
  task_id: string;
  title?: string;
  status: AgentTaskStatus;
}

/** @deprecated  */
export interface AgentStatusUpdate {
  task_id: string;
  status: AgentTaskStatus;
  message: string;
}

export interface AgentEvent {
  agent_run_id: string;
  type: AgentEventType;
  content: string | AgentExecutionPlan | AgentToolCallInfo | AgentObservationInfo | AgentArtifactCard | AgentTaskStartInfo;
  task_id?: string;
  elapsed_ms?: number;
  token_usage?: number;
}

export interface ModeConfig {
  id: string;
  name: string;
  icon: any; // Component type
  value: ModeType;
  description: string;
  themeColor?: 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'slate';
  badge?: string;
}
