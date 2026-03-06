/**
 * Hook to process and style Echarts options
 */
export function useChartOptions() {
    
    const processOption = (rawOption: any) => {
        if (!rawOption) return {};
        const option = JSON.parse(JSON.stringify(rawOption));
        
        // Modern Color Palette
        option.color = [
            '#6366f1', '#3b82f6', '#0ea5e9', '#06b6d4', 
            '#14b8a6', '#10b981', '#84cc16', '#f59e0b', 
            '#f97316', '#ef4444', '#ec4899', '#8b5cf6'
        ];
        
        // Grid
        if (!option.grid) {
            option.grid = { top: '15%', bottom: '12%', left: '3%', right: '4%', containLabel: true };
        } else {
            option.grid.containLabel = true;
        }
        
        // Legend
        if (option.legend) {
            option.legend.type = 'scroll';
            option.legend.bottom = 0;
            option.legend.left = 'center';
        }
        
        // Tooltip
        if (!option.tooltip) {
            option.tooltip = { trigger: 'axis', axisPointer: { type: 'shadow' } };
        }
        option.tooltip.backgroundColor = 'rgba(255, 255, 255, 0.95)';
        option.tooltip.borderColor = '#e2e8f0';
        option.tooltip.textStyle = { color: '#1e293b', fontSize: 12 };
        
        // Graph tweaks
        if (option.series && Array.isArray(option.series)) {
             option.series.forEach((s: any) => {
                 if (s.type === 'graph') {
                     if (!s.force) s.force = { repulsion: 100, edgeLength: 50 };
                     s.roam = true;
                     s.label = { show: true, position: 'right' };
                     s.lineStyle = { color: 'source', curveness: 0.3 };
                 }
             });
        }
    
        return option;
    };

    return {
        processOption
    };
}
