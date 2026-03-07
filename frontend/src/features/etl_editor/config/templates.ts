import { NodeType, SourceType, TransformType, SinkType } from '../types/pipeline';
import type { Node, Edge } from '@vue-flow/core';

export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  nodes: Node[];
  edges: Edge[];
}

const createNode = (id: string, type: NodeType, subType: string, label: string, position: { x: number, y: number }) => ({
  id,
  type: 'custom',
  position,
  data: {
    label,
    type,
    subType,
    status: 'idle'
  }
});

const createEdge = (source: string, target: string) => ({
  id: `e${source}-${target}`,
  source,
  target,
  type: 'smoothstep',
  animated: true
});

export const PIPELINE_TEMPLATES: PipelineTemplate[] = [
  {
    id: 'blank',
    name: '空白流水线',
    description: '从零开始创建一个全新的数据处理流水线',
    icon: 'FilePlus',
    nodes: [],
    edges: []
  },
  {
    id: 'knowledge_graph',
    name: '知识图谱流水线',
    description: '自动提取非结构化数据中的实体关系并构建图谱',
    icon: 'Network',
    nodes: [
      createNode('1', NodeType.SOURCE, SourceType.CRAWLER, '网页爬虫', { x: 100, y: 100 }),
      createNode('2', NodeType.TRANSFORM, TransformType.CLEAN_TEXT, '文本清洗', { x: 100, y: 250 }),
      createNode('3', NodeType.TRANSFORM, TransformType.GRAPH_EXTRACT, '图谱提取', { x: 100, y: 400 }),
      createNode('4', NodeType.SINK, SinkType.NEO4J, 'Neo4j 存储', { x: 100, y: 550 })
    ],
    edges: [
      createEdge('1', '2'),
      createEdge('2', '3'),
      createEdge('3', '4')
    ]
  },
  {
    id: 'vector_store',
    name: '向量库流水线',
    description: '将文本数据转换为向量并存储，用于语义搜索',
    icon: 'Sparkles',
    nodes: [
      createNode('1', NodeType.SOURCE, SourceType.CRAWLER, '网页爬虫', { x: 100, y: 100 }),
      createNode('2', NodeType.TRANSFORM, TransformType.CLEAN_TEXT, '文本清洗', { x: 100, y: 250 }),
      createNode('3', NodeType.TRANSFORM, TransformType.VECTOR_EMBEDDING, '向量嵌入', { x: 100, y: 400 }),
      createNode('4', NodeType.SINK, SinkType.ELASTICSEARCH, 'Elasticsearch', { x: 100, y: 550 })
    ],
    edges: [
      createEdge('1', '2'),
      createEdge('2', '3'),
      createEdge('3', '4')
    ]
  },
  {
    id: 'structured_etl',
    name: '结构化存储流水线',
    description: '同步数据库表结构并进行清洗转换',
    icon: 'Database',
    nodes: [
      createNode('1', NodeType.SOURCE, SourceType.DATABASE, 'MySQL 源', { x: 100, y: 100 }),
      createNode('2', NodeType.TRANSFORM, TransformType.MAP, '字段映射', { x: 100, y: 250 }),
      createNode('3', NodeType.TRANSFORM, TransformType.FILTER, '数据过滤', { x: 100, y: 400 }),
      createNode('4', NodeType.SINK, SinkType.CLICKHOUSE, 'ClickHouse', { x: 100, y: 550 })
    ],
    edges: [
      createEdge('1', '2'),
      createEdge('2', '3'),
      createEdge('3', '4')
    ]
  }
];
