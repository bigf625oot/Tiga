export enum NodeType {
  SOURCE = "source",
  TRANSFORM = "transform",
  SINK = "sink",
  COMBINER = "combiner"
}

export enum SourceType {
  KAFKA = "kafka",
  POSTGRES = "postgres",
  S3 = "s3",
  REST = "rest",
  GENERIC_SQL = "generic_sql",
  SFTP = "sftp",
  CRAWLER = "crawler",
  DATABASE = "database",
  API = "api",
  FILE_UPLOAD = "file_upload"
}

export enum TransformType {
  CLEAN_TEXT = "clean_text",
  AGGREGATE = "aggregate",
  UDF = "udf",
  MAP = "map",
  FILTER = "filter",
  LLM_INTENT = "llm_intent",
  VECTOR_EMBEDDING = "vector_embedding",
  GRAPH_EXTRACT = "graph_extract",
  KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
}

export enum SinkType {
  CLICKHOUSE = "clickhouse",
  NEO4J = "neo4j",
  REDIS = "redis",
  ELASTICSEARCH = "elasticsearch"
}

export enum PipelineStatus {
  CREATED = "created",
  RUNNING = "running",
  STOPPED = "stopped",
  FAILED = "failed"
}

export interface NodeConfig {
  [key: string]: any;
}

// Vue Flow Node Data
export interface NodeData {
  label?: string;
  type?: NodeType;
  subType?: string;
  operator?: string; // e.g., "kafka", "text_process"
  config?: NodeConfig;
  status?: "idle" | "running" | "success" | "error";
  errorMessage?: string;
  metrics?: {
    eps: number;
    latency: number;
  };
  // UI specific
  icon?: string;
  color?: string;
}

export interface Pipeline {
  id: number;
  name: string;
  description?: string;
  status: PipelineStatus;
  dag_config?: {
    nodes: any[]; // Vue Flow Nodes
    edges: any[]; // Vue Flow Edges
  };
  created_at: string;
  updated_at?: string;
  last_run_at?: string;
}

export interface PipelineCreate {
  name: string;
  description?: string;
  dag_config: {
    nodes: any[];
    edges: any[];
  };
}

export interface PipelineUpdate {
  description?: string;
  dag_config?: {
    nodes: any[];
    edges: any[];
  };
}

export interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
  node_id?: string;
}

export interface PipelineRunResponse {
  pipeline_id: number;
  status: string;
  message: string;
}
