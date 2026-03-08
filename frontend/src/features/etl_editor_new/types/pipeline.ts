// --- Enums based on backend connectors ---

export enum NodeType {
  SOURCE = "SOURCE",
  TRANSFORM = "TRANSFORM",
  SINK = "SINK",
}

export enum SourceType {
  KAFKA = "kafka",
  POSTGRES = "postgres",
  S3 = "s3",
  REST = "rest",
  GENERIC_SQL = "generic_sql",
}

export enum TransformType {
  FILTER = "filter",
  MAP = "map",
  CLEAN_TEXT = "clean_text",
  AGGREGATE = "aggregate",
  JOIN = "join",
  UDF = "udf",
}

export enum SinkType {
  CLICKHOUSE = "clickhouse",
  REDIS = "redis",
  NEO4J = "neo4j",
  ELASTICSEARCH = "elasticsearch",
  VECTOR_DB = "vector_db",
}

// --- Configuration Schemas (Can be used with zod later) ---

export interface NodeConfig {
  [key: string]: any;
}

export interface KafkaConfig extends NodeConfig {
  brokers: string;
  topics: string;
  groupId?: string;
  format: "json" | "avro" | "csv";
}

// --- Node Data Interface ---

export interface NodeData {
  label: string;
  type: NodeType;
  subType: SourceType | TransformType | SinkType;
  config: NodeConfig;
  status?: "idle" | "validating" | "ready" | "running" | "error";
  errorMessage?: string;
  metrics?: {
    eps: number; // Events per second
    latency: number; // ms
  };
}

// --- Pipeline Interface ---

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  nodes: any[]; // Vue Flow Nodes
  edges: any[]; // Vue Flow Edges
  createdAt: string;
  updatedAt: string;
  status: "draft" | "active" | "stopped";
}
