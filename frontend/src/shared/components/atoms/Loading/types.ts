export interface ILoadingProps {
  loading?: boolean;
  type?: 'spinner' | 'skeleton-list' | 'skeleton-card';
  text?: string;
  rows?: number;
}
