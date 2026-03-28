<template>
  <div class="prose dark:prose-invert max-w-none text-sm leading-normal markdown-body">
    <component :is="renderedVNode" v-if="renderedVNode" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, h, resolveComponent, shallowRef, onMounted } from 'vue';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeShiki from '@shikijs/rehype';
import { visit } from 'unist-util-visit';

import CodeBlock from './CodeBlock.vue';
import Citation from './Citation.vue';
import DocumentCard from './DocumentCard.vue';
import MermaidRenderer from './MermaidRenderer.vue';
import PlantUMLRenderer from './PlantUMLRenderer.vue';
import AsciiArtRenderer from './AsciiArtRenderer.vue';

const props = defineProps<{
  content: string;
}>();

const emit = defineEmits<{
  (e: 'citation-click', index: number): void;
  (e: 'open-doc-space', id: string): void;
}>();

const renderedVNode = shallowRef<any>(null);

// 1. Remark 插件：提取引用的 [1], [2] 并转化为特殊的 HAST 节点
const remarkCitationPlugin = () => {
  return (tree: any) => {
    visit(tree, 'text', (node: any, index: number | undefined, parent: any) => {
      if (!parent) return;
      
      const citationRegex = /\[(\d+)\]/g;
      if (!citationRegex.test(node.value)) return;
      
      const children: any[] = [];
      let lastIndex = 0;
      let match;
      
      citationRegex.lastIndex = 0; // reset regex
      while ((match = citationRegex.exec(node.value)) !== null) {
        if (match.index > lastIndex) {
          children.push({ type: 'text', value: node.value.slice(lastIndex, match.index) });
        }
        
        children.push({
          type: 'citation',
          data: {
            hName: 'citation',
            hProperties: {
              index: match[1]
            }
          }
        });
        
        lastIndex = citationRegex.lastIndex;
      }
      
      if (lastIndex < node.value.length) {
        children.push({ type: 'text', value: node.value.slice(lastIndex) });
      }
      
      parent.children.splice(index, 1, ...children);
      return index! + children.length; // skip the newly inserted nodes
    });
  };
};

// 1.5. Remark 插件：提取文档引用 doc#1: 《title》
const remarkDocumentCardPlugin = () => {
  return (tree: any) => {
    visit(tree, 'text', (node: any, index: number | undefined, parent: any) => {
      if (!parent) return;
      
      // Some formatting like **doc#6**: 《...》 might be split into multiple nodes by remark.
      // But if it's plain text like "doc#6: 《...》", this will match.
      const docRegex = /doc#\s*(\d+)[*\s]*[:：]?\s*《([^》]+)》/gi;
      if (!docRegex.test(node.value)) return;
      
      const children: any[] = [];
      let lastIndex = 0;
      let match;
      
      docRegex.lastIndex = 0; // reset regex
      while ((match = docRegex.exec(node.value)) !== null) {
        if (match.index > lastIndex) {
          children.push({ type: 'text', value: node.value.slice(lastIndex, match.index) });
        }
        
        children.push({
          type: 'documentCard',
          data: {
            hName: 'document-card',
            hProperties: {
              docId: match[1],
              title: match[2]
            }
          }
        });
        
        lastIndex = docRegex.lastIndex;
      }
      
      if (lastIndex < node.value.length) {
        children.push({ type: 'text', value: node.value.slice(lastIndex) });
      }
      
      parent.children.splice(index, 1, ...children);
      return index! + children.length; // skip the newly inserted nodes
    });
  };
};

// 2. Rehype 插件：在 shiki 处理之前，提取 rawCode
const rehypeExtractRawCode = () => {
  return (tree: any) => {
    visit(tree, 'element', (node: any) => {
      if (node.tagName === 'pre') {
        const codeNode = node.children.find((c: any) => c.tagName === 'code');
        if (codeNode) {
          let rawValue = '';
          visit(codeNode, 'text', (textNode: any) => {
            rawValue += textNode.value;
          });
          node.properties = node.properties || {};
          node.properties.rawCode = rawValue;
          
          const className = codeNode.properties?.className || [];
          const langClass = Array.isArray(className) 
            ? className.find((c: any) => String(c).startsWith('language-'))
            : (String(className).startsWith('language-') ? className : undefined);
            
          if (langClass) {
            node.properties.language = String(langClass).replace('language-', '');
          }
        }
      }
    });
  };
};

// 3. 将 HAST 转换为 Vue VNode 的核心引擎
const renderNode = (node: any, key: string | number = 0): any => {
  if (node.type === 'text') {
    return node.value;
  }
  
  if (node.type === 'root') {
    return (node.children || []).map((c: any, i: number) => renderNode(c, `${key}-${i}`));
  }

  if (node.type === 'element') {
    // 拦截 Citation 节点
    if (node.tagName === 'citation') {
      return h(Citation, {
        index: node.properties.index,
        key,
        onClick: (idx: number | string) => emit('citation-click', typeof idx === 'string' ? parseInt(idx, 10) : idx)
      });
    }

    // 拦截 DocumentCard 节点 (兼容短划线和驼峰)
    if (node.tagName === 'document-card') {
      return h(DocumentCard, {
        docId: node.properties.docId || node.properties['doc-id'],
        title: node.properties.title,
        key,
        onClick: (id: string) => emit('open-doc-space', id)
      });
    }

    // 拦截 Image 节点，处理 PNG 等图片
    if (node.tagName === 'img') {
      const src = node.properties?.src || '';
      const alt = node.properties?.alt || '';
      return h('img', {
        src,
        alt,
        key,
        class: 'max-w-full h-auto rounded-lg shadow-sm border border-border/50 my-2 cursor-pointer hover:opacity-90 transition-opacity',
        onClick: () => window.open(src, '_blank')
      });
    }

    // 拦截 Link 节点，处理 PDF
    if (node.tagName === 'a') {
      const href = node.properties?.href || '';
      if (typeof href === 'string' && href.toLowerCase().endsWith('.pdf')) {
        return h('div', { class: 'my-4 rounded-xl border border-border overflow-hidden bg-card shadow-sm' }, [
          h('div', { class: 'bg-muted/50 px-4 py-2 border-b border-border flex items-center justify-between' }, [
            h('span', { class: 'text-xs font-medium text-foreground flex items-center gap-2' }, [
              h('svg', { class: 'w-4 h-4 text-red-500', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
                h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z' })
              ]),
              'PDF Document'
            ]),
            h('a', { href, target: '_blank', class: 'text-xs text-primary hover:underline' }, 'Open in new tab')
          ]),
          h('iframe', { src: href, class: 'w-full h-[500px] border-none' })
        ]);
      }
    }

    // 拦截 Pre 节点 (由 shiki 增强过，但我们保留了 rawCode 和 language)
    if (node.tagName === 'pre') {
      const rawCode = node.properties?.rawCode || '';
      const language = node.properties?.language || '';
      
      // Mermaid 拦截
      if (language === 'mermaid') {
        return h(MermaidRenderer, { code: rawCode, key });
      }

      // PlantUML 拦截
      if (language === 'plantuml') {
        return h(PlantUMLRenderer, { code: rawCode, key });
      }

      // ASCII Art 拦截
      if (language === 'ascii' || language === 'ascii-art') {
        return h(AsciiArtRenderer, { code: rawCode, key });
      }
      
      // 提取被 shiki 处理后的 code 节点
      const codeAstNodes = (node.children || []).map((c: any, i: number) => renderNode(c, `${key}-${i}`));
      
      return h(CodeBlock, {
        rawCode,
        language,
        codeAstNodes,
        key
      });
    }

    // 标准元素映射
    const props: Record<string, any> = { key };
    
    if (node.properties) {
      for (const [propKey, propValue] of Object.entries(node.properties)) {
        // className 转换为 class
        if (propKey === 'className') {
          props.class = Array.isArray(propValue) ? propValue.join(' ') : propValue;
        } 
        // 过滤内部属性
        else if (propKey !== 'rawCode' && propKey !== 'language') {
          props[propKey] = propValue;
        }
      }
    }

    const children = (node.children || []).map((c: any, i: number) => renderNode(c, `${key}-${i}`));
    return h(node.tagName, props, children);
  }
  
  return null;
};

// 4. 执行 Unified 编译管线
const processMarkdown = async (text: string) => {
  try {
    const processor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkCitationPlugin)
      .use(remarkDocumentCardPlugin)
      .use(remarkRehype, { allowDangerousHtml: true })
      .use(rehypeRaw) // 允许内嵌 HTML，但通过 VNode 渲染保证安全（防 XSS）
      .use(rehypeExtractRawCode)
      .use(rehypeShiki, {
        themes: {
          light: 'vitesse-light',
          dark: 'vitesse-dark',
        },
        defaultColor: false, // 让 shiki 生成 css 变量
        // 忽略不支持的语言，避免报错
        fallbackLanguage: 'text',
      });

    const mdAst = processor.parse(text);
    const hastAst = await processor.run(mdAst);

    const children = renderNode(hastAst);
    renderedVNode.value = h('div', { class: 'contents' }, children);
  } catch (err) {
    console.error('Markdown parsing error:', err);
    // 降级处理
    renderedVNode.value = h('div', { class: 'text-red-500' }, 'Markdown rendering failed');
  }
};

watch(() => props.content, (newContent) => {
  processMarkdown(newContent || '');
}, { immediate: true });

</script>

<style>
/* 添加 shiki 多主题支持变量映射 */
html.dark .shiki,
html.dark .shiki span {
  color: var(--shiki-dark) !important;
  background-color: var(--shiki-dark-bg) !important;
}

html:not(.dark) .shiki,
html:not(.dark) .shiki span {
  color: var(--shiki-light) !important;
  background-color: var(--shiki-light-bg) !important;
}
</style>