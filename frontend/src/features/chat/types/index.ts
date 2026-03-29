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
  | 'kb_retrieval';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  status: StreamStatus;
  blocks: ContentBlock[]; // 有序块数组
}

export interface ThoughtBlock {
  type: 'thought';
  content: string;
  state: 'thinking' | 'collapsed' | 'expanded';
}

export interface PlanStep {
  id: string;
  text: string;
  status: 'pending' | 'running' | 'completed';
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
  state: 'running' | 'success' | 'error';
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
  diff: string; // Unified Diff 格式
  status: 'pending' | 'applied' | 'rejected';
}

export interface SearchSource {
  title: string;
  url: string;
  favicon: string;
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
}

export interface VisualizationBlock {
  type: 'visualization';
  vis_type: 'mermaid' | 'markmap' | 'recharts' | 'echarts';
  data: string;
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
  | PlanBlock
  | TextBlock
  | ToolCallBlock
  | ToolResultBlock
  | TerminalBlock
  | ActionBlock
  | SearchBlock
  | ConfirmationBlock
  | VisualizationBlock
  | ResourceBlock
  | ErrorBlock
  | SandboxBlock
  | KbRetrievalBlock
  | ReferencesBlock
  | SoloLayoutBlock;
