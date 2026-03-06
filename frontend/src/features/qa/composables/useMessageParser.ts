import { computed, type Ref } from 'vue';
import { useMarkdown } from './useMarkdown';

export interface ParsedMessage {
    text: string;
    html: string;
    think: {
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
        let raw = contentRef.value || '';
        const result: ParsedMessage = {
            text: '',
            html: '',
            think: null,
            sql: null,
            chartConfig: null,
            resources: []
        };

        // Helper to extract block and remove from raw
        // Returns the extracted content
        const extractBlock = (regex: RegExp, type: 'think' | 'sql' | 'chart') => {
            let extracted = '';
            let match;
            
            // Loop to find all occurrences and remove them one by one
            // We use a loop because removing a block changes the string indices for subsequent matches if we used matchAll
            // Also, replace(regex, '') with global flag can be tricky with stateful regexes
            while ((match = raw.match(regex)) !== null) {
                const fullMatch = match[0];
                const content = match[1];

                if (type === 'think') {
                    extracted += content + '\n';
                    // Check if this specific block is partial (unclosed)
                    if (!fullMatch.endsWith('</think>')) {
                        // Mark as partial if any block is unclosed (usually the last one)
                         if (!result.think) result.think = { html: '', isPartial: true };
                         else result.think.isPartial = true;
                    }
                } else if (type === 'sql') {
                    // For SQL, we usually only want the last one or merge them?
                    // Let's take the last valid one for now, or merge if multiple?
                    // Typically Vanna returns one SQL. Let's overwrite.
                    result.sql = content.trim();
                } else if (type === 'chart') {
                    try {
                        result.chartConfig = JSON.parse(content.trim());
                    } catch (e) {
                        console.error('Chart JSON parse error', e);
                    }
                }

                // Remove the matched block from raw
                // Use slice to be safe against special chars in fullMatch
                const startIndex = match.index!;
                raw = raw.slice(0, startIndex) + raw.slice(startIndex + fullMatch.length);
            }
            
            return extracted;
        };

        // 1. Extract Think Blocks
        // Regex: Non-greedy match for content. 
        // Handles unclosed tags at end of string via (?:<\/think>|$)
        const thinkContent = extractBlock(/<think>([\s\S]*?)(?:<\/think>|$)/, 'think');
        if (thinkContent) {
            result.think = {
                html: render(thinkContent.trim() || '正在思考...'),
                isPartial: result.think?.isPartial || false
            };
        }

        // 2. Extract Chart Blocks
        // Regex: ::: echarts {json} :::
        extractBlock(/::: echarts\s*([\s\S]*?):::/, 'chart');

        // 3. Extract SQL Blocks
        // Regex: ```sql ... ```
        // Note: We use [\s\S]*? for non-greedy multiline match
        extractBlock(/```sql\s*([\s\S]*?)```/, 'sql');

        // 4. Extract Resources (DocCard & FileCard)
        // This part needs to be careful not to disrupt the text flow if we want to keep them in place?
        // Original logic extracted them but kept text? No, original logic pushed to resources array.
        // Let's keep the original logic for resources but adapt to the new raw
        
        const resourceRegex = /((?:\[DocCard:.*?\]\(.*?\))|(?:(?:::|::: )file[\s\S]*?(?:::|:::)))/g;
        let match;
        const textParts: string[] = [];
        let lastIndex = 0;

        while ((match = resourceRegex.exec(raw)) !== null) {
            // Text before match
            if (match.index > lastIndex) {
                textParts.push(raw.substring(lastIndex, match.index));
            }

            const token = match[0];
            if (token.startsWith('[')) {
                const docM = token.match(/\[DocCard:\s*(.*?)\]\((.*?)\)/);
                if (docM) {
                    result.resources.push({
                        type: 'doc',
                        data: { title: docM[1], id: docM[2] }
                    });
                }
            } else {
                const fileM = token.match(/::: ?file([\s\S]*?):::/);
                if (fileM) {
                    try {
                        const fileData = JSON.parse(fileM[1]);
                        result.resources.push({
                            type: 'file',
                            data: fileData
                        });
                    } catch (e) {
                        console.error('File JSON parse error', e);
                    }
                }
            }
            lastIndex = resourceRegex.lastIndex;
        }
        
        if (lastIndex < raw.length) {
            textParts.push(raw.substring(lastIndex));
        }

        // 5. Remaining Text
        result.text = textParts.join('').trim();
        result.html = render(result.text);

        return result;
    });

    return {
        parsed
    };
}
