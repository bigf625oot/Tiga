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
    if (message.steps && message.steps.length > 0) {
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
        const nextSql = raw.indexOf('```sql', currentPos);
        const nextDoc = raw.indexOf('[DocCard:', currentPos);
        const nextFile = raw.indexOf('::: file', currentPos);
        const nextFileSpace = raw.indexOf(':::  file', currentPos);

        const candidates = [
            { type: 'think', pos: nextThink },
            { type: 'chart', pos: nextChart },
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
