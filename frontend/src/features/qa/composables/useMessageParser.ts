import { computed, type Ref } from 'vue';
import { useMarkdown, isHighlighterReady } from './useMarkdown';

export interface ParsedMessage {
    text: string;
    html: string;
    think: {
        raw: string;
        html: string;
        isPartial: boolean;
    } | null;
    sql: string | null;
    chartConfig: any | null;
    resources: Array<{
        type: 'doc' | 'file';
        data: {
            id: string;
            title?: string;
            name?: string;
            size?: number;
            [key: string]: any;
        };
    }>;
}

/**
 * Hook to parse message content into structured blocks
 * Handles: <think>, ```sql, ::: echarts, ::: file, [DocCard]
 */
export function useMessageParser(contentRef: Ref<string>) {
    const { render } = useMarkdown();

    const parsed = computed<ParsedMessage>(() => {
        // eslint-disable-next-line @typescript-eslint/no-unused-expressions
        isHighlighterReady.value; // ensure re-render when highlighter is ready
        let raw = contentRef.value || '';
        const result: ParsedMessage = {
            text: '',
            html: '',
            think: null,
            sql: null,
            chartConfig: null,
            resources: []
        };

        // One-Pass State Machine Parser
        // Instead of multiple regex passes and O(N^2) string slicing, we scan the string once
        let currentPos = 0;
        const len = raw.length;
        const textParts: string[] = [];

        while (currentPos < len) {
            // Find the next potential tag or block
            const nextThink = raw.indexOf('<think>', currentPos);
            const nextChart = raw.indexOf('::: echarts', currentPos);
            const nextSql = raw.indexOf('```sql', currentPos);
            const nextDoc = raw.indexOf('[DocCard:', currentPos);
            const nextFile = raw.indexOf('::: file', currentPos);
            const nextFileSpace = raw.indexOf(':::  file', currentPos); // handle typo with space

            // Collect all valid next positions
            const candidates = [
                { type: 'think', pos: nextThink },
                { type: 'chart', pos: nextChart },
                { type: 'sql', pos: nextSql },
                { type: 'doc', pos: nextDoc },
                { type: 'file', pos: nextFile !== -1 ? nextFile : nextFileSpace }
            ].filter(c => c.pos !== -1).sort((a, b) => a.pos - b.pos);

            if (candidates.length === 0) {
                // No more blocks, push remaining text
                textParts.push(raw.slice(currentPos));
                break;
            }

            const nextBlock = candidates[0];

            // Push text before the block
            if (nextBlock.pos > currentPos) {
                textParts.push(raw.slice(currentPos, nextBlock.pos));
            }

            if (nextBlock.type === 'think') {
                const startContent = nextBlock.pos + 7; // length of '<think>'
                const endTag = raw.indexOf('</think>', startContent);
                
                if (endTag !== -1) {
                    const content = raw.slice(startContent, endTag);
                    if (!result.think) result.think = { raw: content + '\n', html: '', isPartial: false };
                    else result.think.raw += content + '\n';
                    currentPos = endTag + 8; // length of '</think>'
                } else {
                    // Unclosed think block (streaming)
                    const content = raw.slice(startContent);
                    if (!result.think) result.think = { raw: content + '\n', html: '', isPartial: true };
                    else {
                        result.think.raw += content + '\n';
                        result.think.isPartial = true;
                    }
                    currentPos = len;
                }
            } else if (nextBlock.type === 'chart') {
                const match = raw.slice(nextBlock.pos).match(/^:::\s*echarts\s*([\s\S]*?):::/);
                if (match) {
                    try {
                        result.chartConfig = JSON.parse(match[1].trim());
                    } catch (e) { console.error('Chart JSON parse error', e); }
                    currentPos = nextBlock.pos + match[0].length;
                } else {
                    // If it doesn't match the closing tag, just treat as text and move forward
                    textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 11));
                    currentPos = nextBlock.pos + 11;
                }
            } else if (nextBlock.type === 'sql') {
                const match = raw.slice(nextBlock.pos).match(/^```sql\s*([\s\S]*?)```/);
                if (match) {
                    result.sql = match[1].trim();
                    currentPos = nextBlock.pos + match[0].length;
                } else {
                    textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 6));
                    currentPos = nextBlock.pos + 6;
                }
            } else if (nextBlock.type === 'doc') {
                const match = raw.slice(nextBlock.pos).match(/^\[DocCard:\s*(.*?)\]\((.*?)\)/);
                if (match) {
                    result.resources.push({ type: 'doc', data: { title: match[1], id: match[2] } });
                    currentPos = nextBlock.pos + match[0].length;
                } else {
                    textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 9));
                    currentPos = nextBlock.pos + 9;
                }
            } else if (nextBlock.type === 'file') {
                const match = raw.slice(nextBlock.pos).match(/^:::\s*file([\s\S]*?):::/);
                if (match) {
                    try {
                        result.resources.push({ type: 'file', data: JSON.parse(match[1]) });
                    } catch (e) { console.error('File JSON parse error', e); }
                    currentPos = nextBlock.pos + match[0].length;
                } else {
                    textParts.push(raw.slice(nextBlock.pos, nextBlock.pos + 8));
                    currentPos = nextBlock.pos + 8;
                }
            }
        }

        if (result.think && result.think.raw) {
            result.think.raw = result.think.raw.trim() || '正在思考...';
        }

        result.text = textParts.join('').trim();
        result.html = ''; // Skipping render here to avoid performance issues during streaming

        return result;
    });

    return {
        parsed
    };
}
