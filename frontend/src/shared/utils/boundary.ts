/**
 * Boundary detection module
 * Provides functions to clamp node positions within a canvas.
 */

export interface BoundaryResult {
    x: number;
    y: number;
    clamped: boolean;
}

/**
 * Clamps a node's position (top-left origin) within the canvas boundaries.
 * 
 * Rules:
 * x >= 0
 * y >= 0
 * x <= canvasWidth - nodeWidth
 * y <= canvasHeight - nodeHeight
 * 
 * @param x Current X position
 * @param y Current Y position
 * @param nodeWidth Width of the node
 * @param nodeHeight Height of the node
 * @param canvasWidth Width of the canvas
 * @param canvasHeight Height of the canvas
 * @returns {BoundaryResult} Adjusted position and whether it was clamped
 */
export function clampNodePosition(
    x: number, 
    y: number, 
    nodeWidth: number, 
    nodeHeight: number, 
    canvasWidth: number, 
    canvasHeight: number
): BoundaryResult {
    let newX = x;
    let newY = y;
    let clamped = false;

    // Check X boundaries
    if (newX < 0) {
        newX = 0;
        clamped = true;
    } else if (newX > canvasWidth - nodeWidth) {
        newX = Math.max(0, canvasWidth - nodeWidth); // Ensure not negative if node > canvas
        clamped = true;
    }

    // Check Y boundaries
    if (newY < 0) {
        newY = 0;
        clamped = true;
    } else if (newY > canvasHeight - nodeHeight) {
        newY = Math.max(0, canvasHeight - nodeHeight);
        clamped = true;
    }

    return { x: newX, y: newY, clamped };
}

/**
 * Clamps a node's center position within the canvas boundaries.
 * Useful for graph nodes that are defined by center coordinates and radius.
 * 
 * Rules:
 * x >= radius
 * y >= radius
 * x <= canvasWidth - radius
 * y <= canvasHeight - radius
 * 
 * @param x Center X position
 * @param y Center Y position
 * @param radius Radius of the node
 * @param canvasWidth Width of the canvas
 * @param canvasHeight Height of the canvas
 * @returns {BoundaryResult} Adjusted center position and whether it was clamped
 */
export function clampNodeCenterPosition(
    x: number, 
    y: number, 
    radius: number, 
    canvasWidth: number, 
    canvasHeight: number
): BoundaryResult {
    let newX = x;
    let newY = y;
    let clamped = false;

    // Check X boundaries
    if (newX < radius) {
        newX = radius;
        clamped = true;
    } else if (newX > canvasWidth - radius) {
        newX = Math.max(radius, canvasWidth - radius);
        clamped = true;
    }

    // Check Y boundaries
    if (newY < radius) {
        newY = radius;
        clamped = true;
    } else if (newY > canvasHeight - radius) {
        newY = Math.max(radius, canvasHeight - radius);
        clamped = true;
    }

    return { x: newX, y: newY, clamped };
}
