import { marked, Renderer } from 'marked';
import type { Tokens } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { createHighlighter, type Highlighter } from 'shiki';
import { ref } from 'vue';

let highlighter: Highlighter | null = null;
export const isHighlighterReady = ref(false);

// 初始化 shiki (单例)
const initHighlighter = async () => {
    if (!highlighter) {
        highlighter = await createHighlighter({
            themes: ['github-dark', 'github-light'],
            langs: ['javascript', 'typescript', 'vue', 'python', 'json', 'bash', 'html', 'css', 'sql', 'yaml', 'markdown'],
        });
        isHighlighterReady.value = true;
    }
    return highlighter;
};

// 预加载
initHighlighter().catch(console.error);

/**
 * Hook for markdown rendering with Katex, Shiki syntax highlighting and custom extensions
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

    const createRenderer = (allowHtml: boolean) => {
        const renderer = new Renderer();
        
        // 覆盖默认的 code 渲染以支持代码高亮和复制结构
        renderer.code = (token: Tokens.Code) => {
            const code = token.text;
            const lang = token.lang || 'text';
            
            let highlightedCode = escapeHtml(code);
            
            // 尝试使用 shiki 高亮
            if (highlighter && lang !== 'text') {
                try {
                    // 我们使用一个特殊的占位符类，前端组件后续可以根据主题注入对应的样式
                    highlightedCode = highlighter.codeToHtml(code, { 
                        lang, 
                        theme: 'github-dark' // 默认主题，组件内部可以通过 css 变量处理
                    });
                    
                    // 剥离 shiki 外层 pre 标签，方便我们自定义外壳
                    // shiki 默认会包裹 <pre class="shiki github-dark" style="background-color:#24292e;color:#e1e4e8" tabindex="0"><code>...</code></pre>
                    // 注意：这里我们使用 /<code[^>]*>([\s\S]*?)<\/code>/ 来匹配，更安全
                    const match = highlightedCode.match(/<code[^>]*>([\s\S]*?)<\/code>/);
                    if (match) {
                        highlightedCode = match[1];
                    } else {
                        // 如果没有匹配到，则尝试简单的清理
                        highlightedCode = highlightedCode.replace(/^<pre[^>]*><code[^>]*>/, '').replace(/<\/code><\/pre>$/, '');
                    }
                } catch (e) {
                    console.warn(`Failed to highlight lang: ${lang}`, e);
                    highlightedCode = escapeHtml(code);
                }
            }

            // 返回一个包含语言和代码内容的自定义结构，方便后续组件化处理（如一键复制）
            return `
                <div class="code-block-wrapper relative group my-4 rounded-md overflow-hidden border border-zinc-800 bg-[#0d1117]">
                    <div class="code-block-header flex items-center justify-between px-4 py-1.5 bg-[#161b22] border-b border-zinc-800">
                        <span class="text-xs font-mono text-zinc-400">${lang}</span>
                        <button class="copy-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200" data-code="${escapeHtml(code).replace(/"/g, '&quot;')}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                        </button>
                    </div>
                    <pre class="p-4 m-0 overflow-x-auto text-[13px] leading-relaxed custom-scrollbar text-gray-100 bg-[#0d1117]"><code class="shiki language-${lang}">${highlightedCode}</code></pre>
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
                // Fallback for LLM generated local filenames
                if (!href.startsWith('http') && !href.startsWith('/') && !href.startsWith('data:')) {
                    if (href.startsWith('chart_') || href.startsWith('image_') || href.endsWith('.png') || href.endsWith('.jpg')) {
                        href = `/uploads/${href}`;
                    }
                }
                const title = token.title ? ` title="${escapeHtml(token.title)}"` : '';
                return `<img src="${href}" alt="${escapeHtml(token.text || '')}"${title} class="max-w-full rounded-md shadow-sm my-2" />`;
            };
        }

        return renderer;
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

        // Fix bare sandbox image paths
        inputText = inputText.replace(/(\(|src=['"]?)(chart_[a-zA-Z0-9_]+\.png|image_[a-zA-Z0-9_]+\.jpg)/g, (match, prefix, filename) => {
            return `${prefix}/uploads/${filename}`;
        });

        // Katex Pre-processing
        inputText = inputText.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match, open, formula) => {
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

        // Parse markdown
        const renderer = createRenderer(allowHtml);
        const markedOptions = { ...baseMarkedOptions, renderer };
        let html = marked.parse(inputText, markedOptions) as string;

        // Post-processing
        html = html.replace(/<p>\s*<\/p>/g, '');
        html = html.replace(/\[(\d+)\]/g, (match: string, p1: string) => {
            return `<span class="citation-link cursor-pointer text-indigo-600 hover:underline font-medium mx-0.5" data-index="${p1}">[${p1}]</span>`;
        });

        return html;
    };

    return {
        render,
        initHighlighter
    };
}