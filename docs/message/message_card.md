测试下大模型消息回复的功能与交互体验，要能覆盖thought (思考)、 plan_step (规划步骤)、 tool (工具调用)、 web_search (网络搜索)、 kb_retrieval (知识库片段) 以及最终的 content 。

建议的数据结构：
interface Message {
  role: 'user' | 'assistant';
  parts: Array<
    | { type: 'thought'; content: string; duration?: number } // 思考过程
    | { type: 'plan'; steps: Array<{ text: string; status: 'pending'|'done' }> } // 规划步骤
    | { type: 'text'; content: string } // 最终 Markdown 内容
    | { type: 'tool_call'; toolName: string; args: any; callId: string } // 工具调用
    | { type: 'tool_result'; result: any; callId: string } // 工具执行结果
    | { type: 'search_results'; queries: string[]; sources: Source[] } // 联网搜索
    | { type: 'kb_retrieval'; snippets: Snippet[] } // 知识库检索
  >;
}

