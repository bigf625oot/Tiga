<template>
  <div :class="[proseClass, 'max-w-none text-sm leading-normal markdown-body']">
    <component :is="renderedVNode" v-if="renderedVNode" />
    <div v-else class="contents text-zinc-400 italic text-xs">(正在加载...)</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, h, resolveComponent, shallowRef, onMounted, onUnmounted } from 'vue';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { visit } from 'unist-util-visit';
import CodeBlock from './CodeBlock.vue';
import Citation from './Citation.vue';
import DocumentCard from './DocumentCard.vue';
import MermaidRenderer from './MermaidRenderer.vue';
import PlantUMLRenderer from './PlantUMLRenderer.vue';
import AsciiArtRenderer from './AsciiArtRenderer.vue';
import SourceCard from './SourceCard.vue';

const props = withDefaults(defineProps<{
  content: string;
  proseClass?: string;
}>(), {
  proseClass: 'prose dark:prose-invert'
});

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

// 1.5 Remark 插件：提取 doc# 引用并转化为 document-card 节点
const remarkDocCardPlugin = () => {
  return (tree: any) => {
    visit(tree, 'text', (node: any, index: number | undefined, parent: any) => {
      if (!parent) return;
      
      const docCardRegex = /(?:[•▪·\-\*]\s*)?\*?\*?doc#\s*(\d+)\*?\*?(?:[:：]\s*(?:《([^》\n]+)》|\*([^\*\n]+)\*|([^\n，。；！？\[\]]+)))?/gi;
      if (!docCardRegex.test(node.value)) return;
      
      const children: any[] = [];
      let lastIndex = 0;
      let match;
      
      docCardRegex.lastIndex = 0; // reset regex
      while ((match = docCardRegex.exec(node.value)) !== null) {
        if (match.index > lastIndex) {
          children.push({ type: 'text', value: node.value.slice(lastIndex, match.index) });
        }
        
        const docId = match[1];
        const title = (match[2] || match[3] || match[4] || '').trim();
        
        children.push({
          type: 'document-card',
          data: {
            hName: 'document-card',
            hProperties: {
              'doc-id': docId,
              title: title
            }
          }
        });
        
        lastIndex = docCardRegex.lastIndex;
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

    // 拦截 document-card 节点
    if (node.tagName === 'document-card') {
      const rawDocId = node.properties?.docId || node.properties?.['doc-id'] || node.properties?.docid;
      const docIdStr = String(rawDocId || '').trim();
      return h(DocumentCard, {
        docId: docIdStr,
        title: node.properties?.title || '',
        key,
        class: 'align-middle inline-flex my-1 mx-1',
        onClick: (id: string) => emit('open-doc-space', id)
      });
    }

    // 拦截 Image 节点，处理 PNG 等图片
    if (node.tagName === 'img') {
      let src = node.properties?.src || '';
      if (!src.startsWith('http') && !src.startsWith('/') && !src.startsWith('data:')) {
        if (src.startsWith('chart_') || src.startsWith('image_') || src.endsWith('.png') || src.endsWith('.jpg')) {
          src = `/uploads/${src}`;
        }
      }
      const alt = node.properties?.alt || '';
      return h('img', {
        src,
        alt,
        key,
        class: 'max-w-full h-auto rounded-lg shadow-sm border border-border/50 my-2 cursor-pointer hover:opacity-90 transition-opacity',
        onClick: () => window.open(src, '_blank')
      });
    }

    // 拦截 Link 节点，处理 PDF 和普通链接
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

      // 获取 a 标签内的文本内容作为 title
      let title = '';
      const extractText = (n: any) => {
        if (n.type === 'text') title += n.value;
        if (n.children) n.children.forEach(extractText);
      };
      node.children?.forEach(extractText);

      return h(SourceCard, {
        source: {
          url: href,
          title: title || href
        },
        type: 'web',
        size: 'sm',
        class: 'my-2 inline-flex w-full max-w-sm align-middle', // inline-flex for better alignment
        key
      });
    }

    // 拦截 Table 节点
    if (node.tagName === 'table') {
      const props: Record<string, any> = { key };
      if (node.properties) {
        for (const [propKey, propValue] of Object.entries(node.properties)) {
          if (propKey === 'className') {
            props.class = Array.isArray(propValue) ? propValue.join(' ') : propValue;
          } else if (propKey === 'style' && typeof propValue === 'string') {
            props.style = parseStyle(propValue);
          } else {
            props[propKey] = propValue;
          }
        }
      }
      const children = (node.children || []).map((c: any, i: number) => renderNode(c, `${key}-${i}`));
      const tableVNode = h('table', props, children);
      return h('div', { class: 'table-wrapper custom-scrollbar md-table-wrap overflow-x-auto my-4', key: `${key}-wrap` }, [tableVNode]);
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
      
      const mermaidLangs = new Set([
        'mermaid', 'gantt', 'flowchart', 'sequencediagram', 'classdiagram',
        'statediagram', 'erdiagram', 'journey', 'pie', 'gitgraph',
        'mindmap', 'timeline', 'xychart-beta', 'block-beta'
      ]);

      // Mermaid 拦截
      if (mermaidLangs.has(language.toLowerCase())) {
        let mermaidCode = rawCode.trim();
        // 修复甘特图等语法错误：如果 LLM 没有输出图表类型声明，自动补充
        const lowerLang = language.toLowerCase();
        if (lowerLang !== 'mermaid' && !mermaidCode.toLowerCase().startsWith(lowerLang)) {
            mermaidCode = lowerLang + '\n' + mermaidCode;
        }
        return h(MermaidRenderer, { code: mermaidCode, key });
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

// 4. 执行 Unified 编译管线（同步版本，消除时序竞争）
const processMarkdown = (text: string) => {
  try {
    const sanitizeSchema = {
        ...defaultSchema,
        tagNames: [...(defaultSchema.tagNames || []), 'citation', 'document-card'],
        attributes: {
          ...defaultSchema.attributes,
          '*': [...(defaultSchema.attributes?.['*'] || []), 'className', 'style'],
          'citation': ['index'],
          'document-card': ['docId', 'doc-id', 'docid', 'title'],
        }
      };

    const processor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkMath)
      .use(remarkCitationPlugin)
      .use(remarkDocCardPlugin)
      .use(remarkRehype, { allowDangerousHtml: true })
      .use(rehypeRaw)
      .use(rehypeSanitize, sanitizeSchema)
      .use(rehypeKatex);

    const mdAst = processor.parse(text);
    const hastAst = processor.runSync(mdAst);

    const children = renderNode(hastAst);
    renderedVNode.value = h('div', { class: 'contents' }, children);
  } catch (err) {
    console.error('Markdown parsing error:', err);
    renderedVNode.value = h('div', { class: 'text-red-500' }, 'Markdown rendering failed');
  }
};

// 简单直接：无调度、无锁、无 rAF，每次内容变化直接同步渲染
watch(() => props.content, (newContent) => {
  processMarkdown(newContent || '');
}, { immediate: true });

onUnmounted(() => {
  // 清理
});

</script>
