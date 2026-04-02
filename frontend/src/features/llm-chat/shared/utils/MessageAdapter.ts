import type { Message } from '@/features/llm-chat/shared/types';
import type { 
    ChatMessage, 
    ContentBlock, 
    ToolCallBlock, 
    ToolResultBlock,
    PlanBlock,
    ThoughtBlock,
    TextBlock,
    VisualizationBlock,
    MediaBlock,
    ResourceBlock,
    ErrorBlock,
    ReferencesBlock,
    TerminalBlock,
    ActionBlock,
    KbRetrievalBlock,
    PlanStep
} from '@/features/llm-chat/shared/types';

/**
 * Converts Mermaid mindmap syntax to Markdown outline for Markmap rendering.
 */
function convertMermaidMindmapToMarkdown(code: string): string {
    const lines = code.split('\n');
    const result: string[] = [];
    const indentStack: number[] = [];

    const ID = '[a-zA-Z0-9_-]*';
    const stripMermaidDecorators = (text: string) => {
        return text
            .replace(new RegExp(`^${ID}\\(\\((.+?)\\)\\)$`), '$1')  // circle
            .replace(new RegExp(`^${ID}\\[\\[(.+?)\\]\\]$`), '$1')  // cylinder
            .replace(new RegExp(`^${ID}\\[/(.+?)/\\]$`), '$1')      // trapezoid
            .replace(new RegExp(`^${ID}\\[\\\\(.+?)\\\\\\]$`), '$1') // inv-trap
            .replace(new RegExp(`^${ID}\\((.+?)\\)$`), '$1')        // rounded
            .replace(new RegExp(`^${ID}\\[(.+?)\\]$`), '$1')        // square
            .replace(/^\{\{(.+?)\}\}$/, '$1')                         // hexagon
            .replace(/^>(.+?)$/, '$1')                                // cloud/bang
            .replace(/^"(.+?)"$/, '$1')                               // text
            .replace(/^`(.+?)`$/, '$1')                               // icon
            .replace(/:::[\w\s]+:::?/g, '')                           // class
            .trim();
    };

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === 'mindmap') continue;

        const currentIndent = line.length - line.trimStart().length;

        // Maintain indent stack to precisely determine heading level
        while (indentStack.length > 0 && indentStack[indentStack.length - 1] >= currentIndent) {
            indentStack.pop();
        }
        indentStack.push(currentIndent);

        const level = indentStack.length;
        const text = stripMermaidDecorators(trimmed);

        if (!text) continue;

        result.push(`${'#'.repeat(Math.min(level, 6))} ${text}`);
    }

    return result.join('\n');
}

/**
 * Attempts to parse incomplete JSON strings often encountered in streaming responses.
 */
function partialJsonParse(jsonString: string): any {
    if (!jsonString) return null;
    try {
        return JSON.parse(jsonString);
    } catch (e) {
        let fixed = jsonString;
        const stack: string[] = [];
        
        let inString = false;
        let escapeNext = false;
        
        for (let i = 0; i < fixed.length; i++) {
            const char = fixed[i];
            if (escapeNext) {
                escapeNext = false;
                continue;
            }
            if (char === '\\') {
                escapeNext = true;
                continue;
            }
            if (char === '"') {
                inString = !inString;
                continue;
            }
            if (!inString) {
                if (char === '{') stack.push('}');
                else if (char === '[') stack.push(']');
                else if (char === '}' && stack[stack.length - 1] === '}') stack.pop();
                else if (char === ']' && stack[stack.length - 1] === ']') stack.pop();
            }
        }
        
        if (inString) fixed += '"';
        
        while (stack.length > 0) {
            fixed += stack.pop();
        }
        
        try {
            return JSON.parse(fixed);
        } catch {
            return null; // fallback
        }
    }
}

export interface ProcessorContext {
    readonly message: Message;
    readonly isStreaming: boolean;
    readonly isLast: boolean;
    readonly modeId?: string;
    hasThinkBlock: boolean;
}

export interface MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[];
}

class PlanProcessor implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const { message, isStreaming, isLast, modeId } = ctx;
        const blocks: ContentBlock[] = [];
        
        const SHOW_PLAN_MODES = ['solo', 'team', 'workflow', 'auto_task', 'data_query', 'kg_qa'];
        const shouldShowPlan = modeId && SHOW_PLAN_MODES.includes(modeId);

        if (!message.steps || message.steps.length === 0 || !shouldShowPlan) {
            return blocks;
        }

        const isMsgRunning = isStreaming && isLast;
        const rawTools = message.tools || [];
        const hasMsgError = !!message.error;

        const planSteps: PlanStep[] = message.steps.map((s, idx) => {
            let status = (s as any).status;
            let text = s.content || (s as any).title || (s as any).description || `步骤 ${idx + 1}`;
            if (typeof text !== 'string') text = JSON.stringify(text);

            const stepId = String((s as any).step ?? (s as any).id ?? idx);

            if (!status) {
                // Match tools by step_id, call_id, or name
                const stepTools = rawTools.filter((t: any) => {
                    const toolStepId = String(t.step_id || '');
                    if (toolStepId && toolStepId === stepId) return true;
                    
                    const toolCallId = String(t.id || t.call_id || '');
                    if (toolCallId && toolCallId === stepId) return true;
                    
                    if (t.name && text.includes(t.name)) return true;
                    return false;
                });

                const hasErrorTool = stepTools.some((t: any) => t.status === 'error');
                const hasRunningTool = stepTools.some((t: any) => t.status === 'running');
                
                if (hasErrorTool) {
                    status = 'error';
                } else if (hasRunningTool) {
                    status = 'running';
                } else if (stepTools.length > 0) {
                    status = 'completed';
                } else {
                    if (!isMsgRunning) {
                        status = hasMsgError ? 'pending' : 'completed';
                    } else {
                        status = 'pending';
                    }
                }
            }

            return {
                id: stepId,
                text,
                status: (status === 'completed' || status === 'done') ? 'completed' : (status === 'running' ? 'running' : (status === 'error' ? 'error' : 'pending'))
            } as PlanStep;
        });

        blocks.push({
            type: 'plan',
            steps: planSteps
        } as PlanBlock);

        return blocks;
    }
}

type ToolHandler = (t: any, callId: string, args: any) => ContentBlock[];

const TOOL_HANDLER_MAP: Record<string, ToolHandler> = {
    // Terminal Tools
    ...Object.fromEntries(['execute_command', 'run_command', 'bash', 'shell', 'cmd', 'powershell'].map(name => [name, (t, callId, args) => {
        let command = '';
        if (typeof args === 'string') {
            command = args;
        } else if (typeof args === 'object' && args !== null) {
            command = args.command || args.cmd || args.script;
        }
        
        // Fallback to raw_arguments if parsing failed
        if (!command && t.raw_arguments) {
            command = t.raw_arguments;
        } else if (!command) {
            command = JSON.stringify(args);
        }

        return [{
            type: 'terminal',
            command: command,
            output: typeof t.result === 'string' ? t.result : (t.result ? JSON.stringify(t.result) : ''),
            status: t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success')
        } as TerminalBlock];
    }])),

    // Action Tools
    ...Object.fromEntries(['create_file', 'edit_file', 'delete_file', 'write_file', 'fs_write_file'].map(name => [name, (t, callId, args) => {
        let path = '';
        let content = '';
        if (typeof args === 'object' && args !== null) {
            path = String(args.path || args.file || args.file_path || '');
            content = String(args.content || args.code || '');
        }
        
        let actionType: 'create_file' | 'edit_file' | 'delete_file' = 'edit_file';
        if (name.includes('create') || name === 'write_file' || name === 'fs_write_file') actionType = 'create_file';
        if (name.includes('delete')) actionType = 'delete_file';

        let diff = '';
        if (t.result && typeof t.result === 'string' && t.result.includes('diff')) {
            diff = t.result;
        } else if (actionType === 'create_file') {
            diff = `--- /dev/null\n+++ b/${path}\n@@ -0,0 +1,${content.split('\\n').length} @@\n${content.split('\\n').map((l: string) => '+' + l).join('\\n')}`;
        } else {
            diff = `File: ${path}\nContent:\n${content}`;
        }

        return [{
            type: 'action',
            action_type: actionType,
            path: path,
            description: `Action: ${name} on ${path}`,
            diff: diff,
            status: t.status === 'running' ? 'pending' : (t.status === 'error' ? 'rejected' : 'applied')
        } as ActionBlock];
    }])),

    // Chart Tools
    ...Object.fromEntries(['generate_chart', 'echarts', 'draw_chart', 'plot', 'd3_chart', 'antv_chart'].map(name => [name, (t, callId, args) => {
        if (!t.result) return [];
        const blocks: ContentBlock[] = [];
        
        blocks.push({
            type: 'tool_call',
            call_id: callId,
            tool_name: name,
            arguments: args,
            state: t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success')
        } as ToolCallBlock);

        let chartData = t.result;
        let visType = 'echarts';
        if (name.includes('d3')) visType = 'd3';
        if (name.includes('antv')) visType = 'antv';

        if (typeof chartData === 'string') {
            const parsed = partialJsonParse(chartData);
            if (parsed) {
                chartData = JSON.stringify(parsed);
            } else {
                chartData = JSON.stringify({ type: 'bar', data: chartData });
            }
        } else {
            chartData = JSON.stringify(chartData);
        }

        blocks.push({
            type: 'visualization',
            vis_type: visType as any,
            data: chartData
        } as VisualizationBlock);

        return blocks;
    }])),

    // Knowledge Base Tools
    ...Object.fromEntries(['search_knowledge_base', 'knowledge_retrieval', 'search_docs', 'query_docs'].map(name => [name, (t, callId, args) => {
        const blocks: ContentBlock[] = [];
        blocks.push({
            type: 'tool_call',
            call_id: callId,
            tool_name: name,
            arguments: args,
            state: t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success')
        } as ToolCallBlock);

        if (t.result) {
            let results = [];
            try {
                const parsed = typeof t.result === 'string' ? JSON.parse(t.result) : t.result;
                results = Array.isArray(parsed) ? parsed : (parsed.results || parsed.docs || [parsed]);
            } catch {
                results = [{ title: '检索结果', content: t.result }];
            }

            blocks.push({
                type: 'kb_retrieval',
                query: typeof args === 'object' ? (args.query || args.keyword || JSON.stringify(args)) : args,
                status: 'completed',
                results: results
            } as KbRetrievalBlock);
        }
        return blocks;
    }])),

    // Web Search Tools
    ...Object.fromEntries(['duckduckgo_search', 'google_search', 'tavily_search', 'web_search'].map(name => [name, (t, callId, args) => {
        const blocks: ContentBlock[] = [];
        blocks.push({
            type: 'tool_call',
            call_id: callId,
            tool_name: name,
            arguments: typeof args === 'string' ? {} : args,
            raw_arguments: typeof args === 'string' ? args : undefined,
            state: t.status === 'streaming' ? 'streaming' : (t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success'))
        } as ToolCallBlock);

        if (t.result) {
            blocks.push({
                type: 'tool_result',
                call_id: callId,
                content: typeof t.result === 'string' ? t.result : JSON.stringify(t.result),
                is_error: t.status === 'error'
            } as ToolResultBlock);
        }
        return blocks;
    }]))
};

class ToolProcessor implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const blocks: ContentBlock[] = [];
        const tools = ctx.message.tools || [];
        
        for (let idx = 0; idx < tools.length; idx++) {
            const t = tools[idx];
            const callId = t.id || String(idx);
            const args = t.args || t.arguments || {};
            const toolName = t.name || '';

            const handler = TOOL_HANDLER_MAP[toolName];
            if (handler) {
                blocks.push(...handler(t, callId, args));
            } else {
                // Fallback Generic Tool Call
                blocks.push({
                    type: 'tool_call',
                    call_id: callId,
                    tool_name: toolName,
                    arguments: typeof args === 'string' ? {} : args,
                    raw_arguments: typeof args === 'string' ? args : undefined,
                    state: t.status === 'streaming' ? 'streaming' : (t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success'))
                } as ToolCallBlock);

                if (t.result) {
                    blocks.push({
                        type: 'tool_result',
                        call_id: callId,
                        content: typeof t.result === 'string' ? t.result : JSON.stringify(t.result),
                        is_error: t.status === 'error'
                    } as ToolResultBlock);
                }
            }
        }

        return blocks;
    }
}

class ContentParser implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const blocks: ContentBlock[] = [];
        const raw = ctx.message.content || '';
        let currentPos = 0;
        const len = raw.length;
        const textParts: string[] = [];

        ctx.hasThinkBlock = raw.includes('<think>');

        // Deduplicate thoughts
        if (!ctx.hasThinkBlock) {
            if (ctx.message.reasoning) {
                blocks.push({
                    type: 'thought',
                    content: ctx.message.reasoning,
                    state: (ctx.isStreaming && ctx.isLast) ? 'thinking' : 'collapsed'
                } as ThoughtBlock);
            } else if (ctx.message.meta_data?.reasoning) {
                blocks.push({
                    type: 'thought',
                    content: ctx.message.meta_data.reasoning,
                    state: 'collapsed'
                } as ThoughtBlock);
            }
        }

        while (currentPos < len) {
            const nextThink = raw.indexOf('<think>', currentPos);
            const nextMermaid = raw.indexOf('```mermaid', currentPos);
            const nextMarkmap = raw.indexOf('```markmap', currentPos);
            const nextToolCode = raw.indexOf('```tool_code', currentPos);

            const candidates = [
                { type: 'think', pos: nextThink },
                { type: 'mermaid', pos: nextMermaid },
                { type: 'markmap', pos: nextMarkmap },
                { type: 'tool_code', pos: nextToolCode }
            ].filter(c => c.pos !== -1).sort((a, b) => a.pos - b.pos);

            if (candidates.length === 0) {
                const remaining = raw.slice(currentPos);
                if (remaining) textParts.push(remaining);
                break;
            }

            const nextBlock = candidates[0];

            if (nextBlock.pos > currentPos) {
                const textBefore = raw.slice(currentPos, nextBlock.pos);
                if (textBefore) textParts.push(textBefore);
            }

            // Flush text before special blocks to prevent empty text blocks
            if (textParts.length > 0) {
                const textContent = textParts.join('').trim();
                if (textContent) {
                    blocks.push({ type: 'text', content: textContent } as TextBlock);
                }
                textParts.length = 0;
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
                        state: (ctx.isStreaming && ctx.isLast) ? 'thinking' : 'collapsed'
                    } as ThoughtBlock);
                    currentPos = len;
                }
            } else if (nextBlock.type === 'mermaid') {
                const match = raw.slice(nextBlock.pos).match(/^```mermaid\s*([\s\S]*?)```/);
                if (match) {
                    const code = match[1].trim();
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
                    const partialContent = raw.slice(nextBlock.pos + 10).trim();
                    blocks.push({
                        type: 'visualization',
                        vis_type: 'markmap',
                        data: partialContent
                    } as VisualizationBlock);
                    currentPos = len;
                }
            } else if (nextBlock.type === 'tool_code') {
                const match = raw.slice(nextBlock.pos).match(/^```tool_code\s*([\s\S]*?)(?:```|$)/);
                if (match) {
                    const toolText = match[1].trim();
                    let toolName = 'tool';
                    let args = toolText;
                    
                    const nameMatch = toolText.match(/^([a-zA-Z0-9_]+)\s*\(([\s\S]*?)\)?$/);
                    if (nameMatch) {
                        toolName = nameMatch[1];
                        args = nameMatch[2];
                    }
                    
                    const hasTool = ctx.message.tools?.some((t: any) => t.name === toolName);
                    if (!hasTool) {
                        blocks.push({
                            type: 'tool_call',
                            call_id: `streaming-tool-${Date.now()}`,
                            tool_name: toolName,
                            arguments: {},
                            raw_arguments: args,
                            state: match[0].endsWith('```') ? 'success' : 'streaming'
                        } as ToolCallBlock);
                    }
                    
                    currentPos = nextBlock.pos + match[0].length;
                } else {
                    textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 12));
                    currentPos = nextBlock.pos + 12;
                }
            }
        }

        if (textParts.length > 0) {
            const textContent = textParts.join('').trim();
            if (textContent) {
                blocks.push({ type: 'text', content: textContent } as TextBlock);
            }
        } else if (raw && blocks.filter(b => b.type !== 'thought').length === 0) {
            // Ensure pure text messages without any special blocks are parsed correctly
            blocks.push({ type: 'text', content: raw.trim() } as TextBlock);
        }

        if (ctx.message.chart_config) {
            let visType = 'echarts';
            if (ctx.message.chart_config._type === 'd3') visType = 'd3';
            if (ctx.message.chart_config._type === 'antv') visType = 'antv';
            
            blocks.push({
                type: 'visualization',
                vis_type: visType as any,
                data: JSON.stringify(ctx.message.chart_config)
            } as VisualizationBlock);
        }

        return blocks;
    }
}

class ReferenceProcessor implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const blocks: ContentBlock[] = [];
        if (ctx.message.sources && ctx.message.sources.length > 0) {
            blocks.push({
                type: 'references',
                sources: ctx.message.sources
            } as ReferencesBlock);
        }
        return blocks;
    }
}

class MediaProcessor implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const blocks: ContentBlock[] = [];
        if (ctx.message.media && Array.isArray(ctx.message.media)) {
            ctx.message.media.forEach((m: any) => {
                blocks.push({
                    type: 'media',
                    media_type: m.media_type || 'video',
                    url: m.url,
                    name: m.name,
                    cover_url: m.cover_url,
                    duration: m.duration
                } as MediaBlock);
            });
        }
        return blocks;
    }
}

class ErrorProcessor implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const blocks: ContentBlock[] = [];
        if (ctx.message.error) {
            blocks.push({
                type: 'error',
                message: ctx.message.error,
                can_retry: true
            } as ErrorBlock);
        }
        return blocks;
    }
}

class ArtifactProcessor implements MessageProcessor {
    process(ctx: ProcessorContext): ContentBlock[] {
        const blocks: ContentBlock[] = [];
        const artifactLinks: any[] = [];
        
        if (ctx.message.artifacts && Array.isArray(ctx.message.artifacts)) {
            for (const a of ctx.message.artifacts as any[]) {
                if (a?.url) {
                    artifactLinks.push({
                        name: a.file_name || a.name || '交付文件',
                        url: a.url,
                        type: a.type || 'file',
                        size: a.file_size ?? a.size,
                    });
                } else if (a?.type === 'd3' || a?.type === 'antv') {
                    blocks.push({
                        type: 'visualization',
                        vis_type: a.type as any,
                        data: JSON.stringify(a.data)
                    } as VisualizationBlock);
                }
            }
        }

        const events = ctx.message.stream_events ?? [];
        for (const ev of events) {
            if (ev.event === 'artifact') {
                try {
                    const card: any = ev.raw ?? (typeof ev.content === 'string' ? JSON.parse(ev.content) : ev.content);
                    if (card?.url) {
                        artifactLinks.push({
                            name: card.file_name || card.name || '交付文件',
                            url: card.url,
                            type: card.type || 'file',
                            size: card.file_size ?? card.size,
                        });
                    }
                } catch {
                    // skip
                }
            }
        }

        if (artifactLinks.length > 0) {
            artifactLinks.forEach(art => {
                blocks.push({
                    type: 'resource',
                    resource_type: 'file',
                    data: {
                        id: art.url,
                        title: art.name,
                        size: art.size ? `${(art.size / 1024).toFixed(1)} KB` : undefined
                    }
                } as ResourceBlock);
            });
        }

        return blocks;
    }
}

export function adaptMessageToBlocks(
    message: Message, 
    isStreaming: boolean = false, 
    isLast: boolean = false,
    modeId?: string
): ChatMessage {
    const ctx: ProcessorContext = {
        message,
        isStreaming,
        isLast,
        modeId,
        hasThinkBlock: false
    };

    const processors: MessageProcessor[] = [
        new PlanProcessor(),
        new ToolProcessor(),
        new ContentParser(),
        new ReferenceProcessor(),
        new MediaProcessor(),
        new ErrorProcessor(),
        new ArtifactProcessor()
    ];

    const blocks: ContentBlock[] = processors.flatMap(p => p.process(ctx));

    return {
        id: message.id || String(Date.now()),
        role: message.role as 'user' | 'assistant',
        status: (isStreaming && isLast) ? 'streaming' : 'completed',
        blocks
    };
}
