export interface IGraphNode {
  id: string;
  name?: string;
  type?: string;
  color?: string;
  attributes?: Record<string, any>;
  [key: string]: any;
}

export interface IGraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  [key: string]: any;
}

export type LayoutType = 'force' | 'grid' | 'circle';
