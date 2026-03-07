import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * Hook for markdown rendering with Katex and custom extensions
 */
export function useMarkdown() {
    // Configure marked options once
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    /**
     * Render markdown string to HTML
     * @param {string} text Raw markdown text
     * @returns {string} Rendered HTML
     */
    const render = (text: string): string => {
        if (!text) return '';
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
        let html = marked.parse(inputText) as string;

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
