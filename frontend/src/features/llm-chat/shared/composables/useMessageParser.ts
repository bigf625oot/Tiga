import { computed, type Ref, ref } from 'vue';

export const isHighlighterReady = ref(true);

export interface ParsedMessage {
    text: string;
    html: string;
    think: {
        raw: string;
        html: string;
        isPartial: boolean;
    } | null;
}

/**
 * Hook to parse message content into structured blocks
 * Handles: <think>
 */
export function useMessageParser(contentRef: Ref<string>) {
    const parsed = computed<ParsedMessage>(() => {
        // eslint-disable-next-line @typescript-eslint/no-unused-expressions
        isHighlighterReady.value; // ensure re-render when highlighter is ready
        let raw = contentRef.value || '';
        const result: ParsedMessage = {
            text: '',
            html: '',
            think: null
        };

        // One-Pass State Machine Parser
        // Instead of multiple regex passes and O(N^2) string slicing, we scan the string once
        let currentPos = 0;
        const len = raw.length;
        const textParts: string[] = [];

        while (currentPos < len) {
            // Find the next potential tag or block
            const nextThink = raw.indexOf('<think>', currentPos);

            // Collect all valid next positions
            const candidates = [
                { type: 'think', pos: nextThink }
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
