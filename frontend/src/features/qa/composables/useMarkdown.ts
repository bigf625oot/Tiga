import { marked, Renderer } from 'marked';
import type { Tokens } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * Hook for markdown rendering with Katex and custom extensions
 */
export function useMarkdown() {
    const baseMarkedOptions = {
        breaks: true,
        gfm: true
    } as const;

    const escapeHtml = (value: string) =>
        value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

    const sanitizeHref = (href: string): string => {
        const original = (href || '').trim();
        if (!original) return '';
        if (original.startsWith('#') || original.startsWith('/') || original.startsWith('./') || original.startsWith('../')) {
            return original;
        }

        const compact = original.replace(/[\u0000-\u001F\u007F\s]+/g, '');
        const lower = compact.toLowerCase();
        if (lower.startsWith('javascript:') || lower.startsWith('data:') || lower.startsWith('vbscript:')) {
            return '';
        }

        try {
            const url = new URL(original);
            const protocol = url.protocol.toLowerCase();
            if (protocol === 'http:' || protocol === 'https:' || protocol === 'mailto:' || protocol === 'tel:') {
                return original;
            }
            return '';
        } catch {
            return original;
        }
    };

    const safeRenderer = new Renderer();
    const defaultLink = safeRenderer.link;
    safeRenderer.html = ({ text }: Tokens.HTML | Tokens.Tag) => escapeHtml(text || '');
    safeRenderer.image = ({ text }: Tokens.Image) => escapeHtml(text || '');
    safeRenderer.link = function (token: Tokens.Link) {
        const safeHref = sanitizeHref(token.href);
        if (!safeHref) {
            return this.parser.parseInline(token.tokens, this);
        }
        return defaultLink.call(this, { ...token, href: safeHref });
    };

    /**
     * Render markdown string to HTML
     * @param {string} text Raw markdown text
     * @returns {string} Rendered HTML
     */
    const render = (text: string, options?: { allowHtml?: boolean }): string => {
        if (!text) return '';
        const allowHtml = options?.allowHtml ?? true;
        let inputText = text.trim();

        // Katex Pre-processing
        // Display mode $$...$$ or \[...\]
        inputText = inputText.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, open, formula) => {
            try { 
                return katex.renderToString(formula, { displayMode: true }); 
            } catch { 
                return match; 
            }
        });
        
        // Inline mode \(...\)
        inputText = inputText.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try { 
                return katex.renderToString(formula, { displayMode: false }); 
            } catch { 
                return match; 
            }
        });

        // Parse markdown
        const markedOptions = allowHtml
            ? baseMarkedOptions
            : { ...baseMarkedOptions, renderer: safeRenderer };
        let html = marked.parse(inputText, markedOptions) as string;

        // Post-processing
        // 1. Remove empty paragraphs
        html = html.replace(/<p>\s*<\/p>/g, '');
        
        // 2. Handle [n] citations styling
        html = html.replace(/\[(\d+)\]/g, (match: string, p1: string) => {
            return `<span class="citation-link cursor-pointer text-indigo-600 hover:underline font-medium mx-0.5" data-index="${p1}">[${p1}]</span>`;
        });

        return html;
    };

    return {
        render
    };
}
