export interface Agent {
  name: string;
  icon?: string;
  icon_url?: string;
}

export interface MessageSource {
  title: string;
  docId?: string;
  chunkId?: string;
  nodeId?: string;
  [key: string]: any;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string | number;
  type?: string;
  status?: 'sending' | 'error' | 'success';
  chart_config?: any;
  sources?: MessageSource[];
  [key: string]: any;
}

export interface MessageGroup {
  role: 'user' | 'assistant';
  messages: Message[];
  timestamp: any;
  lastTimestamp: any;
  showTime: boolean;
}
