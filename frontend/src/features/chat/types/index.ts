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
  | 'confirmation';

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
  vis_type: 'mermaid' | 'recharts';
  data: string;
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
  | VisualizationBlock;
