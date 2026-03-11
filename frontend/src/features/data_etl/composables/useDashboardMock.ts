import { ref, computed } from 'vue';
import { NodeType, SourceType, TransformType, SinkType } from '@/features/etl_editor/types/pipeline';

export type Pipeline = {
  id: string;
  name: string;
  processed: number;
  status: 'active' | 'inactive';
};

export type DataSource = {
  id: string;
  name: string;
  type: 'sftp' | 'crawler' | 'database';
  status: 'healthy' | 'warning' | 'error';
  throughput: string;
  active_pipelines: number;
  pipelines: Pipeline[];
};

export type StorageNode = {
  id: string;
  name: string;
  type: 'neo4j' | 'vector';
  status: 'healthy' | 'warning' | 'error';
  metrics: {
    label: string;
    value: string;
    trend?: 'up' | 'down';
    unit?: string;
  }[];
  health_score: number;
};

export type FlowNode = {
  id: string;
  type: NodeType;
  subType: SourceType | TransformType | SinkType;
  label: string;
  subLabel?: string;
  position: { x: number; y: number };
  config?: Record<string, any>;
  stats: {
    total: number;
    pass_rate: number;
    passed: number;
    failed: number;
  };
  throughput?: string;
};

export type LogEntry = {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
};

export type PipelineMetrics = {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down';
  description?: string;
};

export function useDashboardMock() {
  const mode = ref<'normal' | 'abnormal' | 'empty'>('normal');
  const selectedPipelineId = ref<string | null>(null);

  const pipelineMetrics = computed<PipelineMetrics[]>(() => {
    if (!selectedPipelineId.value) return [];
    
    switch (selectedPipelineId.value) {
      case 'p1': // 文档分类流水线
        return [
          { label: '处理文档数', value: 15234, unit: '个', trend: 'up', description: '本周累计处理的文档总量' },
          { label: '分类准确率', value: '98.2', unit: '%', trend: 'up', description: 'AI 模型分类的置信度平均值' },
          { label: '平均耗时', value: '1.2', unit: 's', trend: 'down', description: '单个文档从输入到入库的平均时间' },
          { label: '文档类型数', value: 12, unit: '种', description: '识别到的不同文档类别数量' }
        ];
      case 'p2': // 元数据提取流水线
        return [
          { label: '实体节点数', value: '1.2M', unit: '个', trend: 'up', description: '知识图谱中提取的实体总数' },
          { label: '关系边数', value: '3.5M', unit: '条', trend: 'up', description: '实体之间的关联关系数量' },
          { label: '实体类型数', value: 45, unit: '种', description: '提取的实体类别总数' },
          { label: '图谱密度', value: '0.8', unit: '', description: '图谱中实际边数与可能边数的比率' }
        ];
      default:
        return [
          { label: '实时吞吐', value: '1.0k', unit: '条/秒', description: '当前每秒处理的数据条数' },
          { label: '平均延迟', value: '15', unit: 'ms', description: '数据处理的平均响应时间' },
          { label: '错误率', value: '0.01', unit: '%', description: '处理失败的数据占比' }
        ];
    }
  });

  const dataSources = computed<DataSource[]>(() => {
    if (mode.value === 'empty') return [];
    
    const base: DataSource[] = [
      {
        id: '1',
        name: 'SFTP 文件流',
        type: 'sftp',
        status: 'healthy',
        throughput: '1.2k/s',
        active_pipelines: 2,
        pipelines: [
          { id: 'p1', name: '文档分类流水线', processed: 15234, status: 'active' },
          { id: 'p2', name: '元数据提取流水线', processed: 8452, status: 'active' }
        ]
      },
      {
        id: '2',
        name: 'Tavily 爬虫',
        type: 'crawler',
        status: 'healthy',
        throughput: '850/s',
        active_pipelines: 1,
        pipelines: [
          { id: 'p3', name: '新闻抓取流水线', processed: 8921, status: 'active' }
        ]
      },
      {
        id: '3',
        name: 'SQL 数据库',
        type: 'database',
        status: 'healthy',
        throughput: '2.1k/s',
        active_pipelines: 3,
        pipelines: [
           { id: 'p4', name: '用户数据同步', processed: 12456, status: 'active' },
           { id: 'p5', name: '订单清洗流水线', processed: 45231, status: 'active' },
           { id: 'p6', name: '日志归档流水线', processed: 2311, status: 'inactive' }
        ]
      }
    ];

    if (mode.value === 'abnormal') {
      base[0].status = 'error';
      base[0].throughput = '0/s';
      base[1].status = 'warning';
      base[1].throughput = '120/s';
    }

    return base;
  });

  const storageNodes = computed<StorageNode[]>(() => {
    if (mode.value === 'empty') return [];

    const base: StorageNode[] = [
      {
        id: '1',
        name: 'Neo4j 知识图谱',
        type: 'neo4j',
        status: 'healthy',
        health_score: 98.7,
        metrics: [
          { label: '新增节点', value: '+1,234', trend: 'up' },
          { label: '新增关系', value: '+2,456', trend: 'up' },
          { label: '查询延迟', value: '12ms', trend: 'down' }
        ]
      },
      {
        id: '2',
        name: '向量数据库',
        type: 'vector',
        status: 'healthy',
        health_score: 98.7,
        metrics: [
          { label: '向量索引', value: '45,678', trend: 'up' },
          { label: '索引延迟', value: '8ms', trend: 'down' },
          { label: '相似度查询', value: '892/s' }
        ]
      }
    ];

    if (mode.value === 'abnormal') {
      base[0].status = 'error';
      base[0].health_score = 45.2;
      base[0].metrics[2].value = '1500ms';
      base[0].metrics[2].trend = 'up';
    }

    return base;
  });

  const flowNodes = computed<FlowNode[]>(() => {
    if (mode.value === 'empty' || !selectedPipelineId.value) return [];

    // 根据选中的 pipeline ID 返回不同的节点配置
    switch (selectedPipelineId.value) {
      case 'p1': // 文档分类流水线
        return [
          {
            id: 'n1',
            type: NodeType.SOURCE,
            subType: SourceType.SFTP,
            label: 'SFTP 数据源',
            subLabel: '输入文件',
            position: { x: 100, y: 300 },
            config: {
              host: 'sftp.example.com',
              port: 22,
              username: 'user_docs',
              path: '/incoming/docs',
              file_pattern: '*.pdf'
            },
            stats: { total: 15234, pass_rate: 100, passed: 15234, failed: 0 },
            throughput: '1.2k/s'
          },
          {
            id: 'n2',
            type: NodeType.TRANSFORM,
            subType: TransformType.CLEAN_TEXT,
            label: '文本清洗',
            subLabel: '预处理',
            position: { x: 450, y: 300 },
            config: {
              remove_stopwords: true,
              lowercase: true,
              remove_punctuation: true,
              language: 'zh-CN'
            },
            stats: { total: 15234, pass_rate: 99.5, passed: 15158, failed: 76 },
            throughput: '1.1k/s'
          },
          {
            id: 'n3',
            type: NodeType.TRANSFORM,
            subType: TransformType.LLM_INTENT,
            label: '分类器',
            subLabel: 'LLM 分析',
            position: { x: 800, y: 300 },
            config: {
              model: 'gpt-4',
              temperature: 0.2,
              prompt_template: 'Classify the following document type...',
              categories: ['invoice', 'contract', 'resume']
            },
            stats: { total: 15158, pass_rate: 98.2, passed: 14892, failed: 266 },
            throughput: '1.0k/s'
          },
          {
            id: 'n4',
            type: NodeType.SINK,
            subType: SinkType.ELASTICSEARCH,
            label: 'Elasticsearch',
            subLabel: '索引存储',
            position: { x: 1150, y: 300 },
            config: {
              hosts: ['http://es-node-1:9200'],
              index_name: 'doc_classification',
              shards: 3,
              replicas: 1
            },
            stats: { total: 14892, pass_rate: 100, passed: 14892, failed: 0 },
            throughput: '1.0k/s'
          }
        ];
      
      case 'p2': // 元数据提取流水线
        return [
          {
            id: 'n1',
            type: NodeType.SOURCE,
            subType: SourceType.KAFKA,
            label: 'Kafka 流',
            subLabel: '元数据 Topic',
            position: { x: 100, y: 300 },
            config: {
              bootstrap_servers: 'kafka:9092',
              topic: 'raw_metadata',
              group_id: 'meta_extractor_v1',
              offset: 'latest'
            },
            stats: { total: 8452, pass_rate: 100, passed: 8452, failed: 0 },
            throughput: '850/s'
          },
          {
            id: 'n2',
            type: NodeType.TRANSFORM,
            subType: TransformType.FILTER,
            label: '空值过滤',
            subLabel: '数据质量',
            position: { x: 450, y: 300 },
            config: {
              condition: "record.content != null && record.content != ''",
              drop_nulls: true
            },
            stats: { total: 8452, pass_rate: 92.5, passed: 7818, failed: 634 },
            throughput: '800/s'
          },
          {
            id: 'n3',
            type: NodeType.SINK,
            subType: SinkType.POSTGRES,
            label: 'Postgres 数据库',
            subLabel: '元数据存储',
            position: { x: 800, y: 300 },
            config: {
              host: 'postgres-db',
              port: 5432,
              database: 'metadata_db',
              table: 'extracted_meta'
            },
            stats: { total: 7818, pass_rate: 99.9, passed: 7810, failed: 8 },
            throughput: '800/s'
          }
        ];

      default:
        // 默认返回一个简单的示例
        return [
          {
            id: 'n1',
            type: NodeType.SOURCE,
            subType: SourceType.API,
            label: 'API 数据源',
            subLabel: 'REST 接口',
            position: { x: 200, y: 300 },
            config: { endpoint: '/api/v1/data', method: 'GET' },
            stats: { total: 1000, pass_rate: 100, passed: 1000, failed: 0 },
            throughput: '100/s'
          },
          {
            id: 'n2',
            type: NodeType.SINK,
            subType: SinkType.REDIS,
            label: 'Redis 缓存',
            subLabel: '缓存存储',
            position: { x: 600, y: 300 },
            config: { host: 'redis', port: 6379, db: 0 },
            stats: { total: 1000, pass_rate: 100, passed: 1000, failed: 0 },
            throughput: '100/s'
          }
        ];
    }
  });

  const logs = ref<LogEntry[]>([
    { id: '1', timestamp: '18:17:01', level: 'success', message: '向量化完成: 批次 #8931 (237 条)' },
    { id: '2', timestamp: '18:16:58', level: 'info', message: 'LLM 正在清洗字段: project_name (去除特殊字符)' },
    { id: '3', timestamp: '18:16:55', level: 'success', message: 'Pathway 引擎: 实时增量更新完成' },
    { id: '4', timestamp: '18:16:52', level: 'success', message: 'Pathway 引擎: 实时增量更新完成' },
  ]);

  const setMode = (m: 'normal' | 'abnormal' | 'empty') => {
    mode.value = m;
  };

  const setSelectedPipeline = (id: string | null) => {
    selectedPipelineId.value = id;
  };

  return {
    mode,
    dataSources,
    storageNodes,
    flowNodes,
    logs,
    setMode,
    selectedPipelineId,
    setSelectedPipeline,
    pipelineMetrics
  };
}
