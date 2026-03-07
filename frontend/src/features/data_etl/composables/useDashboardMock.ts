import { ref, computed } from 'vue';

export type DataSource = {
  id: string;
  name: string;
  type: 'sftp' | 'crawler' | 'database';
  status: 'healthy' | 'warning' | 'error';
  throughput: string;
  active_pipelines: number;
  current_pipeline?: {
    name: string;
    processed: number;
  };
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
  type: 'classifier' | 'condition' | 'validator';
  label: string;
  subLabel?: string;
  position: { x: number; y: number };
  stats: {
    total: number;
    pass_rate: number;
    passed: number;
    failed: number;
  };
  throughput?: string; // Input/Output throughput for edges
};

export type LogEntry = {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
};

export function useDashboardMock() {
  const mode = ref<'normal' | 'abnormal' | 'empty'>('normal');

  const dataSources = computed<DataSource[]>(() => {
    if (mode.value === 'empty') return [];
    
    const base: DataSource[] = [
      {
        id: '1',
        name: 'SFTP 文件流',
        type: 'sftp',
        status: 'healthy',
        throughput: '1.2k/s',
        active_pipelines: 1,
        current_pipeline: { name: '问题分类器', processed: 15234 }
      },
      {
        id: '2',
        name: 'Tavily 爬虫',
        type: 'crawler',
        status: 'healthy',
        throughput: '850/s',
        active_pipelines: 1,
        current_pipeline: { name: '条件判断', processed: 8921 }
      },
      {
        id: '3',
        name: 'SQL 数据库',
        type: 'database',
        status: 'healthy',
        throughput: '2.1k/s',
        active_pipelines: 1,
        current_pipeline: { name: 'Pydantic 校验', processed: 12456 }
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
    if (mode.value === 'empty') return [];

    const base: FlowNode[] = [
      {
        id: 'n1',
        type: 'classifier',
        label: '问题分类器',
        subLabel: 'Classifier',
        position: { x: 800, y: 200 },
        stats: { total: 15234, pass_rate: 97.8, passed: 14892, failed: 342 },
        throughput: '1.2k/s'
      },
      {
        id: 'n2',
        type: 'condition',
        label: '条件判断',
        subLabel: 'Condition',
        position: { x: 800, y: 450 },
        stats: { total: 8921, pass_rate: 96.9, passed: 8645, failed: 276 },
        throughput: '850/s'
      },
      {
        id: 'n3',
        type: 'validator',
        label: 'Pydantic 校验',
        subLabel: 'Validator',
        position: { x: 800, y: 700 },
        stats: { total: 12456, pass_rate: 99.1, passed: 12344, failed: 112 },
        throughput: '2.1k/s'
      }
    ];

    if (mode.value === 'abnormal') {
      base[1].stats.pass_rate = 45.0;
      base[1].stats.failed = 4000;
    }

    return base;
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

  return {
    mode,
    dataSources,
    storageNodes,
    flowNodes,
    logs,
    setMode
  };
}
