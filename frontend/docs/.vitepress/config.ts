import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "Tiga 用户操作手册",
  description: "基于 shadcn/ui 组件标准构建的用户指南",
  lang: 'zh-CN',
  base: '/docs/', // 假设部署在 /docs/ 路径下
  
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/introduction' },
      { text: '交互原则', link: '/guide/nielsen' },
      { text: '组件参考', link: '/components/overview' }
    ],

    sidebar: [
      {
        text: '开始使用',
        items: [
          { text: '简介', link: '/guide/introduction' },
          { text: '快速上手', link: '/guide/getting-started' },
          { text: '尼尔森十大原则', link: '/guide/nielsen' }
        ]
      },
      {
        text: '功能模块',
        items: [
          { text: '智能问答', link: '/modules/smart-qa' },
          { text: '知识中心', link: '/modules/knowledge-center' },
          { text: '数据分析', link: '/modules/analytics' }
        ]
      },
      {
        text: '组件库标准',
        items: [
          { text: 'Shadcn/UI 概览', link: '/components/overview' },
          { text: 'Button 按钮', link: '/components/button' },
          { text: 'Card 卡片', link: '/components/card' }
        ]
      }
    ],

    socialLinks: [
      // { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ],
    
    footer: {
      message: '遵循 MIT 协议发布。',
      copyright: 'Copyright © 2024-present Tiga Team'
    }
  }
})
