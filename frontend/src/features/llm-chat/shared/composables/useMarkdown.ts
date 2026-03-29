import { marked, Renderer } from 'marked';
import type { Tokens } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-css-extras';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-tsx';
import 'prismjs/components/prism-markdown';
import 'prismjs/themes/prism-tomorrow.css';

export const escapeHtml = (value: string) =>
    value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

export const highlightCode = (code: string, lang: string): string => {
    const language = lang || 'text';
    const grammar = Prism.languages[language];
    if (grammar) {
        return Prism.highlight(code, grammar, language);
    }
    return escapeHtml(code);
};

/**
 * Hook for markdown rendering with Katex, PrismJS syntax highlighting and custom extensions
 */
export function useMarkdown() {
    const baseMarkedOptions = {
        breaks: true,
        gfm: true
    } as const;

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

    const createRenderer = (allowHtml: boolean) => {
        const renderer = new Renderer();

        // 覆盖默认的 code 渲染以支持代码高亮和复制结构
        renderer.code = (token: Tokens.Code) => {
            const code = token.text;
            const lang = token.lang || 'text';

            const highlightedCode = highlightCode(code, lang);

            return `
                <div class="code-block-wrapper relative group my-4 rounded-lg overflow-hidden border border-zinc-800 bg-[#0d1117]">
                    <div class="code-block-header flex items-center justify-between px-4 py-1.5 bg-[#161b22] border-b border-zinc-800">
                        <span class="text-xs font-mono text-zinc-400">${escapeHtml(lang)}</span>
                        <button class="copy-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200" data-code="${escapeHtml(code)}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                        </button>
                    </div>
                    <pre class="p-4 m-0 overflow-x-auto text-sm leading-relaxed custom-scrollbar text-gray-100 bg-[#0d1117]"><code class="language-${escapeHtml(lang)}">${highlightedCode}</code></pre>
                </div>
            `;
        };

        if (!allowHtml) {
            const defaultLink = renderer.link;
            renderer.html = ({ text }: Tokens.HTML | Tokens.Tag) => escapeHtml(text || '');
            renderer.image = ({ text }: Tokens.Image) => escapeHtml(text || '');
            renderer.link = function (token: Tokens.Link) {
                const safeHref = sanitizeHref(token.href);
                if (!safeHref) {
                    return this.parser.parseInline(token.tokens, this);
                }
                return defaultLink.call(this, { ...token, href: safeHref });
            };
        } else {
            renderer.image = (token: Tokens.Image) => {
                let href = token.href || '';
                if (!href.startsWith('http') && !href.startsWith('/') && !href.startsWith('data:')) {
                    if (href.startsWith('chart_') || href.startsWith('image_') || href.endsWith('.png') || href.endsWith('.jpg')) {
                        href = `/uploads/${href}`;
                    }
                }
                const title = token.title ? ` title="${escapeHtml(token.title)}"` : '';
                return `<img src="${href}" alt="${escapeHtml(token.text || '')}"${title} class="max-w-full rounded-md shadow-sm my-2" />`;
            };
        }

        // 覆盖默认的 table 渲染以支持响应式横向滚动
        const defaultTable = renderer.table.bind(renderer);
        renderer.table = (token: Tokens.Table) => {
            const html = defaultTable(token);
            return `<div class="table-wrapper custom-scrollbar">\n${html}\n</div>`;
        };

        return renderer;
    };

    /**
     * Render markdown string to HTML
     */
    const render = (text: string, options?: { allowHtml?: boolean }): string => {
        if (!text) return '';
        const allowHtml = options?.allowHtml ?? true;
        let inputText = text.trim();

        inputText = inputText.replace(/(\(|src=['"]?)(chart_[a-zA-Z0-9_]+\.png|image_[a-zA-Z0-9_]+\.jpg)/g, (_match, prefix, filename) => {
            return `${prefix}/uploads/${filename}`;
        });

        // Katex Pre-Processing
        inputText = inputText.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, _open, formula) => {
            try {
                return katex.renderToString(formula, { displayMode: true });
            } catch {
                return match;
            }
        });

        inputText = inputText.replace(/\\\(([\s\S]*?)\\\)/g, (match, formula) => {
            try {
                return katex.renderToString(formula, { displayMode: false });
            } catch {
                return match;
            }
        });

        // Pre-process for document cards
        inputText = inputText.replace(/(?:[•▪·\-\*]\s*)?\*?\*?doc#\s*(\d+)\*?\*?(?:[:：]\s*|\s+)(?:《([^》\n]+)》|\*([^\*\n]+)\*|([^\n，。；！？,.;!?(（\[\]]+))/gi, (match, docId, t1, t2, t3) => {
            const title = (t1 || t2 || t3 || '').trim();
            if (title) {
                return `\n\n<document-card doc-id="${docId}" title="${escapeHtml(title)}"></document-card>\n\n`;
            }
            return match;
        });

        const renderer = createRenderer(allowHtml);
        const markedOptions = { ...baseMarkedOptions, renderer };
        let html = marked.parse(inputText, markedOptions) as string;

        // Post-processing
        html = html.replace(/<p>\s*<\/p>/g, '');
        html = html.replace(/\[(\d+)\]/g, (match: string, p1: string) => {
            return `<span class="citation-link cursor-pointer text-indigo-600 hover:underline font-medium mx-0.5" data-index="${p1}">[${p1}]</span>`;
        });

        html = html.replace(/<p>\s*(<document-card[^>]*><\/document-card>)\s*<\/p>/gi, '$1');

        return html;
    };

    return {
        render,
        escapeHtml,
        highlightCode
    };
}
