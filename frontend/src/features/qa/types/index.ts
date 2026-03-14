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

export interface Message {
  role: Role;
  content: string;
  timestamp?: string | number;
  type?: string;
  status?: MessageStatus;
  reasoning?: string;
  steps?: { content: string; step: number }[];
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
  knowledge_config?: string | { document_ids?: string[]; knowledge_base_ids?: string[] };
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  members?: Agent[];
}

export type ModeType = 'chat' | 'workflow' | 'auto_task';

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

export interface ModeConfig {
  id: string;
  name: string;
  icon: any; // Component type
  value: ModeType;
  description: string;
  themeColor?: 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'slate';
}
