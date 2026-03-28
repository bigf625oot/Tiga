export type Role = 'user' | 'assistant' | 'system';

export type MessageStatus = 'sending' | 'sent' | 'error' | 'success';

export interface MessageSource {
  title: string;
  docId?: string;
  chunkId?: string;
  nodeId?: string;
  [key: string]: any;
}

export interface ChartConfig {
  type: string;
  data: any;
  options?: any;
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
  updated_at: string;
}

// ─── AgentEvent 协议类型（与 backend/app/schemas/agent_event.py 严格对应）───

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

// tool_output 事件内容
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

// task_start 事件内容（替代旧的 AgentStatusUpdate）
export interface AgentTaskStartInfo {
  task_id: string;
  title?: string;
  status: AgentTaskStatus;
}

/** @deprecated 使用 AgentTaskStartInfo 替代 */
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
