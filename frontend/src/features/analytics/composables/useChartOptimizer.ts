import * as echarts from 'echarts';

/**
 * Hook to optimize ECharts options with a modern, polished UI.
 */
export function useChartOptimizer() {
    
    // Modern Color Palette (Indigo/Blue/Violet theme)
    const colorPalette = [
        '#6366f1', // Indigo 500
        '#3b82f6', // Blue 500
        '#0ea5e9', // Sky 500
        '#06b6d4', // Cyan 500
        '#14b8a6', // Teal 500
        '#8b5cf6', // Violet 500
        '#ec4899', // Pink 500
        '#f43f5e', // Rose 500
        '#f59e0b', // Amber 500
    ];

    const optimizeOption = (rawOption: any) => {
        if (!rawOption) return {};
        const option = JSON.parse(JSON.stringify(rawOption));

        // 1. Global Settings
        option.color = colorPalette;
        option.backgroundColor = 'transparent';
        
        // 2. Typography & Text
        const fontStack = '"Inter", "system-ui", "-apple-system", sans-serif';
        const textMain = '#334155'; // Slate 700
        const textSub = '#64748b';  // Slate 500

        if (option.textStyle) {
            option.textStyle.fontFamily = fontStack;
        } else {
            option.textStyle = { fontFamily: fontStack };
        }

        // 3. Tooltip (Glassmorphism)
        if (!option.tooltip) option.tooltip = {};
        Object.assign(option.tooltip, {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: [12, 16],
            textStyle: { color: textMain, fontSize: 13 },
            extraCssText: 'box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); border-radius: 12px; backdrop-filter: blur(4px);',
            trigger: option.tooltip.trigger || 'axis',
            axisPointer: {
                type: 'line',
                lineStyle: { color: '#cbd5e1', width: 1, type: 'dashed' },
                shadowStyle: { color: 'rgba(226, 232, 240, 0.4)' }
            }
        });

        // 4. Grid (Clean layout)
        if (!option.grid) {
            option.grid = { top: 60, right: 30, bottom: 40, left: 20, containLabel: true };
        } else {
            option.grid.containLabel = true;
            // Ensure padding for standard layouts
            if (option.grid.top === undefined) option.grid.top = 60;
            if (option.grid.bottom === undefined) option.grid.bottom = 40;
        }

        // 5. Axes (Minimalist)
        const axisCommon = {
            axisLine: { show: true, lineStyle: { color: '#e2e8f0' } },
            axisTick: { show: false },
            axisLabel: { color: textSub, fontSize: 11, margin: 12 },
            splitLine: { show: true, lineStyle: { color: '#f1f5f9', type: 'dashed' } }
        };

        if (option.xAxis) {
            if (!Array.isArray(option.xAxis)) option.xAxis = [option.xAxis];
            option.xAxis.forEach((axis: any) => {
                Object.assign(axis, axisCommon);
                axis.splitLine.show = false; // Usually hide X split lines
            });
        }
        if (option.yAxis) {
            if (!Array.isArray(option.yAxis)) option.yAxis = [option.yAxis];
            option.yAxis.forEach((axis: any) => {
                Object.assign(axis, axisCommon);
                axis.axisLine.show = false; // Hide Y axis line for cleaner look
            });
        }

        // 6. Legend (Pill style)
        if (option.legend) {
            Object.assign(option.legend, {
                bottom: 0,
                left: 'center',
                itemWidth: 14,
                itemHeight: 14,
                itemGap: 20,
                icon: 'circle',
                textStyle: { color: textSub, fontSize: 12 }
            });
            // Clear borders/padding
            delete option.legend.borderWidth;
            delete option.legend.padding;
        }

        // 7. Title (Modern)
        if (option.title) {
            const titles = Array.isArray(option.title) ? option.title : [option.title];
            titles.forEach((t: any) => {
                // If title is centered in a pie chart (often used for total count)
                if ((t.left === 'center' || t.left === '50%') && (t.top === 'center' || t.top === 'middle' || t.top === '50%')) {
                    t.textStyle = { color: textMain, fontSize: 24, fontWeight: 700, fontFamily: fontStack };
                    t.subtextStyle = { color: textSub, fontSize: 13, fontFamily: fontStack };
                } else {
                    // Standard top title
                    if (!t.left) t.left = 'center'; // Default center
                    if (!t.top) t.top = 10;
                    t.textStyle = { color: textMain, fontSize: 16, fontWeight: 600, fontFamily: fontStack };
                    t.subtextStyle = { color: textSub, fontSize: 12, fontFamily: fontStack };
                }
            });
        }

        // 8. Series Optimization
        if (option.series) {
            option.series.forEach((s: any, index: number) => {
                const color = colorPalette[index % colorPalette.length];

                // --- Bar Chart ---
                if (s.type === 'bar') {
                    s.barMaxWidth = 40;
                    s.itemStyle = {
                        borderRadius: [6, 6, 0, 0],
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: color },
                            { offset: 1, color: hexToRgba(color, 0.6) }
                        ])
                    };
                    // Add subtle shadow
                    s.showBackground = true;
                    s.backgroundStyle = { color: '#f8fafc', borderRadius: [6, 6, 0, 0] };
                }

                // --- Line Chart ---
                if (s.type === 'line') {
                    s.smooth = true;
                    s.symbol = 'circle';
                    s.symbolSize = 8;
                    s.itemStyle = { 
                        color: color, 
                        borderWidth: 2, 
                        borderColor: '#fff',
                        shadowColor: 'rgba(0,0,0,0.1)',
                        shadowBlur: 5
                    };
                    s.lineStyle = { width: 3, shadowColor: hexToRgba(color, 0.3), shadowBlur: 10, shadowOffsetY: 5 };
                    
                    // Area Style (Gradient)
                    s.areaStyle = {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: hexToRgba(color, 0.4) },
                            { offset: 1, color: hexToRgba(color, 0.0) }
                        ]),
                        opacity: 0.8
                    };
                }

                // --- Pie/Donut Chart ---
                if (s.type === 'pie') {
                    // Default to Donut
                    if (!s.radius) s.radius = ['50%', '70%'];
                    if (!s.center) s.center = ['50%', '50%']; // Perfectly centered
                    
                    s.itemStyle = {
                        borderRadius: 8,
                        borderColor: '#ffffff',
                        borderWidth: 3
                    };
                    
                    // Pad angle for separation
                    // s.padAngle = 5; // Needs ECharts 5.5+, safe to add? Let's check version or just add it (ignored if not supported)
                    
                    // Label
                    s.label = {
                        show: true,
                        formatter: '{b}\n{d}%',
                        color: textMain,
                        fontSize: 12
                    };
                    
                    // Center label for donut (if not present via Title)
                    // We rely on ECharts Title for the center text usually.
                    // But we can enhance emphasis
                    s.emphasis = {
                        scale: true,
                        scaleSize: 10,
                        itemStyle: {
                            shadowBlur: 20,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.2)'
                        },
                        label: { show: true, fontWeight: 'bold' }
                    };
                }
            });
        }

        return option;
    };

    // Helper: Hex to RGBA
    const hexToRgba = (hex: string, alpha: number) => {
        let r = 0, g = 0, b = 0;
        // 3 digits
        if (hex.length === 4) {
            r = parseInt("0x" + hex[1] + hex[1]);
            g = parseInt("0x" + hex[2] + hex[2]);
            b = parseInt("0x" + hex[3] + hex[3]);
        } 
        // 6 digits
        else if (hex.length === 7) {
            r = parseInt("0x" + hex[1] + hex[2]);
            g = parseInt("0x" + hex[3] + hex[4]);
            b = parseInt("0x" + hex[5] + hex[6]);
        }
        return `rgba(${r},${g},${b},${alpha})`;
    };

    return {
        optimizeOption
    };
}
