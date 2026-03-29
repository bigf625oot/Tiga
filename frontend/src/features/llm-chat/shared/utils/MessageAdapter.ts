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
    ResourceBlock,
    ErrorBlock,
    ReferencesBlock,
    SoloLayoutBlock,
    TerminalBlock,
    ActionBlock
} from '@/features/llm-chat/shared/types';

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
    // We now use sequential blocks for solo mode too
    /*
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
    */

    // Default Pattern: Sequential Blocks
    // Only show execution plan for complex modes, hide for 'quick' and 'chat'
    const SHOW_PLAN_MODES = ['solo', 'team', 'workflow', 'auto_task', 'data_query', 'kg_qa'];
    const shouldShowPlan = modeId && SHOW_PLAN_MODES.includes(modeId);

    if (message.steps && message.steps.length > 0 && shouldShowPlan) {
        const isMsgRunning = isStreaming && isLast;
        const rawTools = message.tools || [];
        const hasMsgError = !!message.error;

        blocks.push({
            type: 'plan',
            steps: message.steps.map((s, idx, arr) => {
                let status = (s as any).status;
                let text = s.content || (s as any).title || (s as any).description || `步骤 ${idx + 1}`;
                if (typeof text !== 'string') text = JSON.stringify(text);

                if (!status) {
                    const chunkSize = Math.ceil(rawTools.length / arr.length) || 1;
                    const stepTools = rawTools.filter((_: any, ti: number) =>
                        ti >= idx * chunkSize && ti < (idx + 1) * chunkSize
                    );
                    const hasErrorTool = stepTools.some((t: any) => t.status === 'error');
                    const hasRunningTool = stepTools.some((t: any) => t.status === 'running');
                    const stepToolsLen = stepTools.length;

                    if (hasErrorTool) {
                        status = 'error';
                    } else if (hasRunningTool) {
                        status = 'running';
                    } else if (stepToolsLen > 0) {
                        status = 'completed';
                    } else {
                        if (!isMsgRunning) {
                            const anyError = hasMsgError || arr.some((_, aIdx) => {
                                const cSize = Math.ceil(rawTools.length / arr.length) || 1;
                                const sTools = rawTools.filter((_: any, ti: number) => ti >= aIdx * cSize && ti < (aIdx + 1) * cSize);
                                return sTools.some((t: any) => t.status === 'error');
                            });
                            status = anyError ? 'pending' : 'completed';
                        } else {
                            const allPrevDone = arr.slice(0, idx).every((_, pIdx) => {
                                const cSize = Math.ceil(rawTools.length / arr.length) || 1;
                                const sTools = rawTools.filter((_: any, ti: number) => ti >= pIdx * cSize && ti < (pIdx + 1) * cSize);
                                return sTools.length > 0 && !sTools.some((t: any) => t.status === 'error') && !sTools.some((t: any) => t.status === 'running');
                            });
                            if (allPrevDone) {
                                status = 'running';
                            } else {
                                status = 'pending';
                            }
                        }
                    }
                }

                return {
                    id: String((s as any).step ?? (s as any).id ?? idx),
                    text,
                    status: (status === 'completed' || status === 'done') ? 'completed' : (status === 'running' ? 'running' : (status === 'error' ? 'error' : 'pending'))
                };
            })
        } as PlanBlock);
    }

    // 2. Process tools status
    if (message.tools && message.tools.length > 0) {
        message.tools.forEach((t: any, idx: number) => {
            const callId = t.id || String(idx);
            const args = t.args || t.arguments || {};
            const toolName = t.name || '';
            
            // Map command execution tools to TerminalBlock
            const terminalTools = ['execute_command', 'run_command', 'bash', 'shell', 'cmd', 'powershell'];
            if (terminalTools.includes(toolName)) {
                let command = '';
                if (typeof args === 'string') {
                    command = args;
                } else if (typeof args === 'object' && args !== null) {
                    command = args.command || args.cmd || args.script || JSON.stringify(args);
                }
                
                blocks.push({
                    type: 'terminal',
                    command: command,
                    output: typeof t.result === 'string' ? t.result : (t.result ? JSON.stringify(t.result) : ''),
                    status: t.status === 'error' ? 'error' : (t.status === 'running' ? 'running' : 'success')
                } as TerminalBlock);
                return;
            }

            // Map file editing tools to ActionBlock
            const actionTools = ['create_file', 'edit_file', 'delete_file', 'write_file', 'fs_write_file'];
            if (actionTools.includes(toolName)) {
                let path = '';
                let content = '';
                if (typeof args === 'object' && args !== null) {
                    path = String(args.path || args.file || args.file_path || '');
                    content = String(args.content || args.code || '');
                }
                
                let actionType: 'create_file' | 'edit_file' | 'delete_file' = 'edit_file';
                if (toolName.includes('create') || toolName === 'write_file' || toolName === 'fs_write_file') actionType = 'create_file';
                if (toolName.includes('delete')) actionType = 'delete_file';

                // We try to use the diff from result if available, otherwise just show content
                let diff = '';
                if (t.result && typeof t.result === 'string' && t.result.includes('diff')) {
                    diff = t.result;
                } else if (actionType === 'create_file') {
                    diff = `--- /dev/null\n+++ b/${path}\n@@ -0,0 +1,${content.split('\\n').length} @@\n${content.split('\\n').map((l: string) => '+' + l).join('\\n')}`;
                } else {
                    diff = `File: ${path}\nContent:\n${content}`;
                }

                blocks.push({
                    type: 'action',
                    action_type: actionType,
                    path: path,
                    description: `Action: ${toolName} on ${path}`,
                    diff: diff,
                    status: t.status === 'running' ? 'pending' : (t.status === 'error' ? 'rejected' : 'applied')
                } as ActionBlock);
                return;
            }

            // Fallback to generic ToolCallBlock
            blocks.push({
                type: 'tool_call',
                call_id: callId,
                tool_name: toolName,
                arguments: args,
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
        const nextToolCode = raw.indexOf('```tool_code', currentPos);

        const candidates = [
            { type: 'think', pos: nextThink },
            { type: 'chart', pos: nextChart },
            { type: 'mermaid', pos: nextMermaid },
            { type: 'markmap', pos: nextMarkmap },
            { type: 'sql', pos: nextSql },
            { type: 'doc', pos: nextDoc },
            { type: 'file', pos: nextFile !== -1 ? nextFile : nextFileSpace },
            { type: 'tool_code', pos: nextToolCode }
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
                
                const hasTool = message.tools?.some((t: any) => t.name === toolName);
                if (!hasTool) {
                    blocks.push({
                        type: 'tool_call',
                        call_id: `streaming-tool-${Date.now()}`,
                        tool_name: toolName,
                        arguments: args,
                        state: match[0].endsWith('```') ? 'success' : 'running'
                    } as ToolCallBlock);
                }
                
                currentPos = nextBlock.pos + match[0].length;
            } else {
                // Should not happen with the regex, but just in case
                textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 12));
                currentPos = nextBlock.pos + 12;
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

    // 6. Process Artifacts
    const artifactLinks: any[] = [];
    if (message.artifacts && Array.isArray(message.artifacts)) {
        for (const a of message.artifacts as any[]) {
            if (a?.url) {
                artifactLinks.push({
                    name: a.file_name || a.name || '交付文件',
                    url: a.url,
                    type: a.type || 'file',
                    size: a.file_size ?? a.size,
                });
            }
        }
    }
    const events = message.stream_events ?? [];
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
                    id: art.url, // using url as id
                    title: art.name,
                    size: art.size ? `${(art.size / 1024).toFixed(1)} KB` : undefined
                }
            } as ResourceBlock);
        });
    }

    return {
        id: message.id || String(Date.now()),
        role: message.role as 'user' | 'assistant',
        status: (isStreaming && isLast) ? 'streaming' : 'completed',
        blocks
    };
}
