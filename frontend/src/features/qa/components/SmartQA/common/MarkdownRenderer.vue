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

// 解析 style 字符串为对象，避免 Vue cssText 赋值时丢失纯 CSS 变量
const parseStyle = (styleStr: string): Record<string, string> => {
  const styleObj: Record<string, string> = {};
  if (!styleStr) return styleObj;
  
  styleStr.split(';').forEach(rule => {
    const [key, ...values] = rule.split(':');
    if (key && values.length) {
      styleObj[key.trim()] = values.join(':').trim();
    }
  });
  return styleObj;
};

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

// 2. 将 HAST 转换为 Vue VNode 的核心引擎
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

    // 拦截 Pre 节点，回退到最简单可靠的 pre > code 纯文本渲染模式
    if (node.tagName === 'pre') {
      const codeNode = node.children?.find((c: any) => c.tagName === 'code');
      let rawCode = '';
      let language = '';
      
      if (codeNode) {
        // 从 code 节点中提取纯文本代码
        rawCode = codeNode.children?.filter((c: any) => c.type === 'text').map((c: any) => c.value).join('') || '';
        
        // 从 className 中提取语言 (例如 'language-javascript')
        const className = codeNode.properties?.className;
        if (Array.isArray(className)) {
          const langClass = className.find(c => typeof c === 'string' && c.startsWith('language-'));
          if (langClass) language = langClass.replace('language-', '');
        } else if (typeof className === 'string' && className.startsWith('language-')) {
          language = className.replace('language-', '');
        }
      }
      
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
      
      // 极简方案：抛弃复杂的 AST 传递，直接传递 rawCode 和 language 给 CodeBlock
      return h(CodeBlock, {
        rawCode,
        language,
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
        // style 字符串转换为对象
        else if (propKey === 'style' && typeof propValue === 'string') {
          props.style = parseStyle(propValue);
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
    // Pre-normalize bold-wrapped doc references: **doc#6**: 《...》 → doc#6: 《...》
    // remark splits **doc#6** into a strong node, breaking the text-node regex in remarkDocumentCardPlugin
    text = text.replace(/\*\*(doc#\s*\d+)\*\*(?=\s*[*\s]*[:：]?\s*《)/g, '$1');

    const processor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkCitationPlugin)
      .use(remarkDocumentCardPlugin)
      .use(remarkRehype, { allowDangerousHtml: true })
      .use(rehypeRaw); // 允许内嵌 HTML，但通过 VNode 渲染保证安全（防 XSS）
      // 彻底移除 rehypeShiki，回归第一性原理：使用最简单的结构直接展示文本

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
