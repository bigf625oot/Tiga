import type { Message } from '../../qa/types';
import type { 
    ChatMessage, 
    ContentBlock, 
    ToolCallBlock, 
    ToolResultBlock,
    PlanBlock,
    ThoughtBlock,
    TextBlock,
    VisualizationBlock,
    ResourceBlock,
    ErrorBlock,
    ReferencesBlock,
    SoloLayoutBlock
} from '../types';

/**
 * Converts Mermaid mindmap syntax to Markdown outline for Markmap rendering.
 * Mermaid mindmap uses indentation-based hierarchy; we map each level to a
 * heading depth so Markmap can build the interactive tree.
 *
 * Input:
 *   mindmap
 *     root((Agent综述))
 *       Branch A
 *         Leaf
 *
 * Output:
 *   # Agent综述
 *   ## Branch A
 *   ### Leaf
 */
function convertMermaidMindmapToMarkdown(code: string): string {
    const lines = code.split('\n');
    const result: string[] = [];
    let baseIndent = -1;
    let indentStep = 2; // detected from first two levels

    for (const line of lines) {
        const trimmed = line.trim();
        // Skip directive line and blanks
        if (!trimmed || trimmed === 'mindmap') continue;

        const currentIndent = line.length - line.trimStart().length;

        if (baseIndent === -1) {
            baseIndent = currentIndent;
        } else if (indentStep === 2 && currentIndent > baseIndent) {
            // Detect actual indent step from the first child
            indentStep = Math.max(1, currentIndent - baseIndent);
        }

        // Relative indent → heading level (root = h1)
        const level = Math.max(1, Math.round((currentIndent - baseIndent) / indentStep) + 1);

        // Strip Mermaid node shape decorators.
        // Mermaid allows an optional ASCII identifier before the shape, e.g. root((label)).
        // Match with-prefix forms first, then bare forms.
        const ID = '[a-zA-Z0-9_-]*'; // optional node identifier
        const text = trimmed
            .replace(new RegExp(`^${ID}\\(\\((.+?)\\)\\)$`), '$1')  // id((label)) circle
            .replace(new RegExp(`^${ID}\\[\\[(.+?)\\]\\]$`), '$1')  // id[[label]] cylinder
            .replace(new RegExp(`^${ID}\\[/(.+?)/\\]$`),    '$1')   // id[/label/] trapezoid
            .replace(new RegExp(`^${ID}\\[\\\\(.+?)\\\\\\]$`), '$1') // id[\label\] inv-trap
            .replace(new RegExp(`^${ID}\\((.+?)\\)$`),      '$1')   // id(label) rounded
            .replace(new RegExp(`^${ID}\\[(.+?)\\]$`),      '$1')   // id[label] square
            .replace(/^\{\{(.+?)\}\}$/, '$1')                         // {{hexagon}}
            .replace(/^>(.+?)$/, '$1')                                // >cloud/bang
            .replace(/^"(.+?)"$/, '$1')                               // "text"
            .replace(/^`(.+?)`$/, '$1')                               // `icon`
            .replace(/:::[\w\s]+:::?/g, '')                           // :::class:::
            .trim();

        if (!text) continue;

        result.push(`${'#'.repeat(Math.min(level, 6))} ${text}`);
    }

    return result.join('\n');
}

export function adaptMessageToBlocks(
    message: Message, 
    isStreaming: boolean = false, 
    isLast: boolean = false,
    modeId?: string
): ChatMessage {
    const blocks: ContentBlock[] = [];

    // Strategy Pattern: if Solo mode, use a specific unified layout block
    if (modeId === 'solo') {
        blocks.push({
            type: 'solo_layout',
            original_message: message,
            is_last: isLast,
            is_streaming: isStreaming
        } as SoloLayoutBlock);
        
        return {
            id: message.id || String(Date.now()),
            role: message.role as 'user' | 'assistant',
            status: (isStreaming && isLast) ? 'streaming' : 'completed',
            blocks
        };
    }

    // Default Pattern: Sequential Blocks
    // Only show execution plan for complex modes, hide for 'quick' and 'chat'
    const SHOW_PLAN_MODES = ['solo', 'team', 'workflow', 'auto_task', 'data_query', 'kg_qa'];
    const shouldShowPlan = modeId && SHOW_PLAN_MODES.includes(modeId);

    if (message.steps && message.steps.length > 0 && shouldShowPlan) {
        blocks.push({
            type: 'plan',
            steps: message.steps.map((s, i) => ({
                id: String(i),
                text: s.content,
                status: (s as any).status === 'completed' ? 'completed' : ((s as any).status === 'running' ? 'running' : 'pending')
            }))
        } as PlanBlock);
    }

    // 2. Process tools status
    if (message.tools && message.tools.length > 0) {
        message.tools.forEach((t: any, idx: number) => {
            const callId = t.id || String(idx);
            blocks.push({
                type: 'tool_call',
                call_id: callId,
                tool_name: t.name,
                arguments: t.args || t.arguments || {},
                state: t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success')
            } as ToolCallBlock);

            if (t.result) {
                blocks.push({
                    type: 'tool_result',
                    call_id: callId,
                    content: typeof t.result === 'string' ? t.result : JSON.stringify(t.result),
                    is_error: t.status === 'error'
                } as ToolResultBlock);
            }
        });
    }

    // 3. Process Content using One-Pass logic (adapted from useMessageParser)
    let raw = message.content || '';
    let currentPos = 0;
    const len = raw.length;
    const textParts: string[] = [];

    // Add standalone reasoning if not present in content
    if (message.reasoning && !raw.includes('<think>')) {
        blocks.push({
            type: 'thought',
            content: message.reasoning,
            state: (isStreaming && isLast) ? 'thinking' : 'collapsed'
        } as ThoughtBlock);
    } else if (message.meta_data?.reasoning && !raw.includes('<think>')) {
        blocks.push({
            type: 'thought',
            content: message.meta_data.reasoning,
            state: 'collapsed'
        } as ThoughtBlock);
    }

    while (currentPos < len) {
        const nextThink = raw.indexOf('<think>', currentPos);
        const nextChart = raw.indexOf('::: echarts', currentPos);
        const nextMermaid = raw.indexOf('```mermaid', currentPos);
        const nextMarkmap = raw.indexOf('```markmap', currentPos);
        const nextSql = raw.indexOf('```sql', currentPos);
        const nextDoc = raw.indexOf('[DocCard:', currentPos);
        const nextFile = raw.indexOf('::: file', currentPos);
        const nextFileSpace = raw.indexOf(':::  file', currentPos);

        const candidates = [
            { type: 'think', pos: nextThink },
            { type: 'chart', pos: nextChart },
            { type: 'mermaid', pos: nextMermaid },
            { type: 'markmap', pos: nextMarkmap },
            { type: 'sql', pos: nextSql },
            { type: 'doc', pos: nextDoc },
            { type: 'file', pos: nextFile !== -1 ? nextFile : nextFileSpace }
        ].filter(c => c.pos !== -1).sort((a, b) => a.pos - b.pos);

        if (candidates.length === 0) {
            textParts.push(raw.slice(currentPos));
            break;
        }

        const nextBlock = candidates[0];

        if (nextBlock.pos > currentPos) {
            textParts.push(raw.slice(currentPos, nextBlock.pos));
            // Flush accumulated text before pushing special blocks
            if (textParts.length > 0 && textParts.join('').trim()) {
                blocks.push({
                    type: 'text',
                    content: textParts.join('').trim()
                } as TextBlock);
                textParts.length = 0;
            }
        }

        if (nextBlock.type === 'think') {
            const startContent = nextBlock.pos + 7;
            const endTag = raw.indexOf('</think>', startContent);
            
            if (endTag !== -1) {
                blocks.push({
                    type: 'thought',
                    content: raw.slice(startContent, endTag).trim() || '正在思考...',
                    state: 'collapsed'
                } as ThoughtBlock);
                currentPos = endTag + 8;
            } else {
                blocks.push({
                    type: 'thought',
                    content: raw.slice(startContent).trim() || '正在思考...',
                    state: 'thinking'
                } as ThoughtBlock);
                currentPos = len;
            }
        } else if (nextBlock.type === 'chart') {
            const match = raw.slice(nextBlock.pos).match(/^:::\s*echarts\s*([\s\S]*?):::/);
            if (match) {
                blocks.push({
                    type: 'visualization',
                    vis_type: 'echarts',
                    data: match[1].trim()
                } as VisualizationBlock);
                currentPos = nextBlock.pos + match[0].length;
            } else {
                textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 11));
                currentPos = nextBlock.pos + 11;
            }
        } else if (nextBlock.type === 'mermaid') {
            const match = raw.slice(nextBlock.pos).match(/^```mermaid\s*([\s\S]*?)```/);
            if (match) {
                const code = match[1].trim();
                // Auto-convert Mermaid mindmap → Markmap for better visuals
                if (/^mindmap\b/.test(code)) {
                    blocks.push({
                        type: 'visualization',
                        vis_type: 'markmap',
                        data: convertMermaidMindmapToMarkdown(code)
                    } as VisualizationBlock);
                } else {
                    blocks.push({
                        type: 'visualization',
                        vis_type: 'mermaid',
                        data: code
                    } as VisualizationBlock);
                }
                currentPos = nextBlock.pos + match[0].length;
            } else {
                // Incomplete fenced block (still streaming)
                const partialCode = raw.slice(nextBlock.pos + 10).trim();
                if (/^mindmap\b/.test(partialCode)) {
                    blocks.push({
                        type: 'visualization',
                        vis_type: 'markmap',
                        data: convertMermaidMindmapToMarkdown(partialCode)
                    } as VisualizationBlock);
                } else {
                    blocks.push({
                        type: 'visualization',
                        vis_type: 'mermaid',
                        data: partialCode
                    } as VisualizationBlock);
                }
                currentPos = len;
            }
        } else if (nextBlock.type === 'markmap') {
            const match = raw.slice(nextBlock.pos).match(/^```markmap\s*([\s\S]*?)```/);
            if (match) {
                blocks.push({
                    type: 'visualization',
                    vis_type: 'markmap',
                    data: match[1].trim()
                } as VisualizationBlock);
                currentPos = nextBlock.pos + match[0].length;
            } else {
                // Incomplete fenced block (still streaming) — render partial markdown
                const partialContent = raw.slice(nextBlock.pos + 10).trim();
                blocks.push({
                    type: 'visualization',
                    vis_type: 'markmap',
                    data: partialContent
                } as VisualizationBlock);
                currentPos = len;
            }
        } else if (nextBlock.type === 'sql') {
            const match = raw.slice(nextBlock.pos).match(/^```sql\s*([\s\S]*?)```/);
            if (match) {
                // We keep sql as text for now, but formatted
                blocks.push({
                    type: 'text',
                    content: `\`\`\`sql\n${match[1].trim()}\n\`\`\``
                } as TextBlock);
                currentPos = nextBlock.pos + match[0].length;
            } else {
                textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 6));
                currentPos = nextBlock.pos + 6;
            }
        } else if (nextBlock.type === 'doc') {
            const match = raw.slice(nextBlock.pos).match(/^\[DocCard:\s*(.*?)\]\((.*?)\)/);
            if (match) {
                blocks.push({
                    type: 'resource',
                    resource_type: 'doc',
                    data: { title: match[1], id: match[2] }
                } as ResourceBlock);
                currentPos = nextBlock.pos + match[0].length;
            } else {
                textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 9));
                currentPos = nextBlock.pos + 9;
            }
        } else if (nextBlock.type === 'file') {
            const match = raw.slice(nextBlock.pos).match(/^:::\s*file([\s\S]*?):::/);
            if (match) {
                try {
                    blocks.push({
                        type: 'resource',
                        resource_type: 'file',
                        data: JSON.parse(match[1])
                    } as ResourceBlock);
                } catch (e) { console.error('File JSON parse error', e); }
                currentPos = nextBlock.pos + match[0].length;
            } else {
                textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 8));
                currentPos = nextBlock.pos + 8;
            }
        }
    }

    if (textParts.length > 0 && textParts.join('').trim()) {
        blocks.push({
            type: 'text',
            content: textParts.join('').trim()
        } as TextBlock);
    }

    // Process standalone chart_config (legacy)
    if (message.chart_config) {
        blocks.push({
            type: 'visualization',
            vis_type: 'echarts',
            data: JSON.stringify(message.chart_config)
        } as VisualizationBlock);
    }

    // 4. Process References
    if (message.sources && message.sources.length > 0) {
        blocks.push({
            type: 'references',
            sources: message.sources
        } as ReferencesBlock);
    }

    // 5. Process Error
    if (message.error) {
        blocks.push({
            type: 'error',
            message: message.error,
            can_retry: true
        } as ErrorBlock);
    }

    return {
        id: message.id || String(Date.now()),
        role: message.role as 'user' | 'assistant',
        status: (isStreaming && isLast) ? 'streaming' : 'completed',
        blocks
    };
}
