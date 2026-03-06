import type { LayoutType } from '../../../types/graph';

export interface IGraphToolbarProps {
  currentLayout?: LayoutType; // Optional in toolbar if not used
  fullscreen: boolean;
  scale: number;
  scope?: string;
  showScopeToggle?: boolean;
  selectedNodeId?: string | null;
}
