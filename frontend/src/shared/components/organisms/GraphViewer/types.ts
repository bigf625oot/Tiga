import type { IGraphNode, IGraphEdge, LayoutType } from '@/shared/types/graph';

export interface IGraphViewerProps {
  nodes: Record<string, IGraphNode>;
  edges: Record<string, IGraphEdge>;
  hiddenTypes?: string[];
  colorMap?: Record<string, string>;
  scope?: string;
  showScopeToggle?: boolean;
  showToolbar?: boolean;
  loading?: boolean;
}
