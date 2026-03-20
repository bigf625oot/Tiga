import { ref, computed } from 'vue';

const savedLocale = localStorage.getItem('tiga_locale') as 'zh-CN' | 'en-US' | 'ja-JP' | 'ko-KR';
const locale = ref<'zh-CN' | 'en-US' | 'ja-JP' | 'ko-KR'>(savedLocale || 'zh-CN');

const messages = {
  'zh-CN': {
    taskView: '任务',
    codeView: '代码',
    terminal: '终端',
    runResults: '沙箱',
    aiWaiting: 'AI 正在等待输入以即时生成…',
    aiGenerating: 'AI 已自主启动，正在实时生成中…',
    aiBadge: 'AI 自动生成',
    zeroHuman: '零人工参与',
    autoMode: '全自动模式',
    app: {
      nav: {
        task: '任务',
        agent: '智能体',
        knowledge: '知识中心',
      },
      newChat: '新建对话',
      systemSettings: '系统设置',
      userManual: '用户操作手册',
      allSessions: '全部任务记录',
      allSessionsDesc: '查看并管理您的历史对话任务。',
      searchTaskName: '搜索任务名称...',
      noTasksFound: '未找到相关任务',
      defaultAssistant: '默认助手',
      newConversation: '新对话',
      deleteSuccess: '删除成功',
      deleteFailed: '删除失败',
    },
    // Agent Status Dashboard
    agentStatus: {
      progress: '进度',
      duration: '耗时',
      status: {
        running: '运行中',
        completed: '已完成',
        failed: '失败',
        idle: '空闲',
        paused: '已暂停'
      },
      phases: {
        init: '初始化',
        planning: '规划',
        execution: '执行',
        review: '复盘',
        finished: '完成',
        ready: '就绪',
        executing: '正在执行代码'
      },
      metrics: {
        cpu: 'CPU 使用率',
        memory: '内存占用',
        network: '网络流量',
        errors: '错误数',
        events: '次'
      }
    },
    // Sandbox
    sandbox: {
      tabs: {
        result: '执行结果',
        env: '环境信息'
      },
      env: {
        title: '沙箱环境配置',
        runtime: '运行时',
        resourceLimits: '资源限制',
        cpu: 'CPU',
        memory: '内存',
        network: '网络',
        egress: '出站流量',
        workspace: '工作区'
      },
      status: {
        noData: '暂无数据生成…',
        error: '执行出错',
        cancelled: '任务已取消',
        copied: '已复制到剪贴板',
        copyFailed: '复制失败',
        cancel: '取消'
      },
      output: {
        preview: '输出预览',
        generatedImages: '生成图片',
        thinking: '思考过程'
      }
    }
  },
  'en-US': {
    taskView: 'AI Task Flow',
    codeView: 'AI Code Gen',
    terminal: 'Auto Terminal',
    runResults: 'Live Sandbox',
    aiWaiting: 'AI is waiting for input to generate instantly...',
    aiGenerating: 'AI has started autonomously, generating in real-time...',
    aiBadge: 'AI Generated',
    zeroHuman: 'Zero Human Intervention',
    autoMode: 'Fully Autonomous',
    app: {
      nav: {
        task: 'Tasks',
        agent: 'Agents',
        knowledge: 'Knowledge',
      },
      newChat: 'New Chat',
      systemSettings: 'System Settings',
      userManual: 'User Manual',
      allSessions: 'All Sessions',
      allSessionsDesc: 'View and manage your chat sessions.',
      searchTaskName: 'Search session name...',
      noTasksFound: 'No sessions found',
      defaultAssistant: 'Default Assistant',
      newConversation: 'New Chat',
      deleteSuccess: 'Deleted',
      deleteFailed: 'Delete failed',
    },
    // Agent Status Dashboard
    agentStatus: {
      progress: 'Progress',
      duration: 'Duration',
      status: {
        running: 'Running',
        completed: 'Finished',
        failed: 'Failed',
        idle: 'Idle',
        paused: 'Paused'
      },
      phases: {
        init: 'Init',
        planning: 'Planning',
        execution: 'Execution',
        review: 'Review',
        finished: 'Finished',
        ready: 'Ready',
        executing: 'Executing Code'
      },
      metrics: {
        cpu: 'CPU Usage',
        memory: 'Memory',
        network: 'Network',
        errors: 'Errors',
        events: 'events'
      }
    },
    // Sandbox
    sandbox: {
      tabs: {
        result: 'Result',
        env: 'Environment'
      },
      env: {
        title: 'Sandbox Environment',
        runtime: 'Runtime',
        resourceLimits: 'Resource Limits',
        cpu: 'CPU',
        memory: 'Memory',
        network: 'Network',
        egress: 'Egress',
        workspace: 'Workspace'
      },
      status: {
        noData: 'No data generated...',
        error: 'Execution Error',
        cancelled: 'Task cancelled',
        copied: 'Copied to clipboard',
        copyFailed: 'Copy failed',
        cancel: 'Cancel'
      },
      output: {
        preview: 'Output Preview',
        generatedImages: 'Generated Images',
        thinking: 'Thinking Process'
      }
    }
  },
  'ja-JP': {
    taskView: 'AIタスクフロー',
    codeView: 'AIコード生成',
    terminal: '自動ターミナル',
    runResults: 'リアルタイムサンドボックス',
    aiWaiting: 'AIは即時生成のための入力を待っています...',
    aiGenerating: 'AIが自律的に起動し、リアルタイムで生成中です...',
    aiBadge: 'AI自動生成',
    zeroHuman: '人工介入なし',
    autoMode: '全自動モード',
    app: {
      nav: {
        task: 'タスク',
        agent: 'エージェント',
        knowledge: 'ナレッジ',
      },
      newChat: '新規チャット',
      systemSettings: 'システム設定',
      userManual: 'ユーザーマニュアル',
      allSessions: '全セッション',
      allSessionsDesc: '会話履歴を確認・管理します。',
      searchTaskName: 'セッション名を検索...',
      noTasksFound: '該当するセッションがありません',
      defaultAssistant: 'デフォルトアシスタント',
      newConversation: '新規チャット',
      deleteSuccess: '削除しました',
      deleteFailed: '削除に失敗しました',
    }
  },
  'ko-KR': {
    taskView: 'AI 태스크 플로우',
    codeView: 'AI 코드 생성',
    terminal: '자동 터미널',
    runResults: '실시간 샌드박스',
    aiWaiting: 'AI가 즉시 생성을 위해 입력을 기다리고 있습니다...',
    aiGenerating: 'AI가 자율적으로 시작되어 실시간으로 생성 중입니다...',
    aiBadge: 'AI 자동 생성',
    zeroHuman: '인간 개입 없음',
    autoMode: '완전 자동 모드',
    app: {
      nav: {
        task: '작업',
        agent: '에이전트',
        knowledge: '지식',
      },
      newChat: '새 채팅',
      systemSettings: '시스템 설정',
      userManual: '사용자 매뉴얼',
      allSessions: '전체 세션',
      allSessionsDesc: '대화 세션을 보고 관리합니다.',
      searchTaskName: '세션 이름 검색...',
      noTasksFound: '관련 세션이 없습니다',
      defaultAssistant: '기본 어시스턴트',
      newConversation: '새 채팅',
      deleteSuccess: '삭제됨',
      deleteFailed: '삭제 실패',
    }
  }
};

export function useI18n() {
  const t = (key: string) => {
    const keys = key.split('.');
    let value: any = messages[locale.value];
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key;
      }
    }
    return value;
  };

  const setLocale = (lang: 'zh-CN' | 'en-US' | 'ja-JP' | 'ko-KR') => {
    locale.value = lang;
    localStorage.setItem('tiga_locale', lang);
  };

  return {
    t,
    locale,
    setLocale
  };
}
