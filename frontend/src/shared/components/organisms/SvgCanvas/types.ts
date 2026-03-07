export interface SvgNode {
    id: string;
    x: number;
    y: number;
    width: number;
    height: number;
    label?: string;
    color?: string;
    selected?: boolean;
}

export interface BoundaryClampEvent {
    nodeId: string;
    x: number;
    y: number;
}
