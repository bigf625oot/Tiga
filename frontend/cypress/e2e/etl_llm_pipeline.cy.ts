describe('ETL Pipeline with LLM Intent Node', () => {
  beforeEach(() => {
    // 访问 ETL 编辑器页面
    cy.visit('/etl/editor');
  });

  it('should allow dragging, configuring, and saving an LLM Intent node', () => {
    // 1. 验证左侧侧边栏存在 LLM 意图识别组件
    cy.get('[data-test="sidebar-item-llm_intent"]')
      .should('contain.text', 'LLM 意图识别');

    // 2. 拖拽组件到画布 (模拟拖拽)
    // 注意：实际拖拽在 Cypress 中通常需要 cypress-drag-drop 插件或触发特定事件
    const dataTransfer = new DataTransfer();
    cy.contains('LLM 意图识别').trigger('dragstart', { dataTransfer });
    cy.get('.vue-flow__pane').trigger('drop', { 
      dataTransfer,
      clientX: 300,
      clientY: 300
    });

    // 3. 选中节点以打开属性面板
    // 假设新添加的节点有特定的类或ID，这里选择最后一个节点
    cy.get('.vue-flow__node').last().click();

    // 4. 验证属性面板打开并加载了 LLM 配置组件
    cy.get('.sheet-content').should('be.visible');
    cy.contains('模型 (Model)').should('be.visible');

    // 5. 配置参数
    // 选择模型
    cy.get('button[role="combobox"]').click();
    cy.contains('GPT-4').click();

    // 输入 Prompt
    cy.contains('提示模板').parent().find('textarea')
      .clear()
      .type('分析以下文本的用户意图：{{text}}');

    // 输入 JSON Schema
    cy.contains('输出约束').parent().find('textarea')
      .type('{"type": "object", "properties": {"intent": {"type": "string"}}}');

    // 展开高级选项
    cy.contains('高级参数').click();
    
    // 调整超时时间
    cy.contains('超时时间').parent().find('input')
      .clear()
      .type('5000');

    // 启用 A/B 测试
    cy.contains('启用 A/B 测试').parent().find('button[role="switch"]')
      .click();

    // 6. 模拟保存操作
    cy.intercept('POST', '/api/v1/pipelines', {
      statusCode: 200,
      body: { id: 123, status: 'success' }
    }).as('savePipeline');

    cy.get('button').contains('保存').click();

    // 7. 验证发送的请求数据
    cy.wait('@savePipeline').then((interception) => {
      const body = interception.request.body;
      const llmNode = body.dag_config.nodes.find((n: any) => n.data.subType === 'llm_intent');
      
      expect(llmNode).to.exist;
      expect(llmNode.data.config.model).to.equal('gpt-4');
      expect(llmNode.data.config.prompt_template).to.include('分析以下文本');
      expect(llmNode.data.config.timeout).to.equal(5000);
      expect(llmNode.data.config.ab_testing_enabled).to.be.true;
    });
  });

  it('should handle runtime errors gracefully', () => {
    // 模拟运行失败
    cy.intercept('POST', '/api/v1/pipelines/123/run', {
      statusCode: 200,
      body: { 
        status: 'error',
        message: 'LLM API Timeout'
      }
    }).as('runPipeline');

    // 点击运行
    cy.get('button').contains('运行').click();

    // 验证错误提示
    cy.wait('@runPipeline');
    cy.contains('LLM API Timeout').should('be.visible');
  });

  it('should allow configuring Filter node with Visual Builder', () => {
    // 1. 拖拽 Filter 组件
    const dataTransfer = new DataTransfer();
    cy.contains('数据过滤').trigger('dragstart', { dataTransfer });
    cy.get('.vue-flow__pane').trigger('drop', { 
      dataTransfer,
      clientX: 500,
      clientY: 300
    });

    // 2. 选中 Filter 节点
    cy.get('.vue-flow__node').last().click();

    // 3. 验证 Visual Builder 出现
    cy.contains('可视化构建器').should('be.visible');

    // 4. 添加条件
    cy.contains('添加条件').click();
    
    // 输入字段名 intent
    cy.get('input[placeholder*="Field"]').last().type('intent');
    
    // 选择操作符 == (默认)
    
    // 输入值 refund
    cy.get('input[placeholder="Value"]').last().type('refund');

    // 验证生成的代码预览
    cy.contains("col('intent') == 'refund'").should('exist');

    // 5. 切换逻辑为 OR
    cy.get('button[role="combobox"]').contains('AND').click();
    cy.contains('OR').click();

    // 6. 保存并验证
    cy.intercept('POST', '/api/v1/pipelines', {
      statusCode: 200,
      body: { id: 124, status: 'success' }
    }).as('savePipelineWithFilter');

    cy.get('button').contains('保存').click();

    cy.wait('@savePipelineWithFilter').then((interception) => {
      const body = interception.request.body;
      const filterNode = body.dag_config.nodes.find((n: any) => n.data.subType === 'filter');
      
      expect(filterNode).to.exist;
      // 验证生成的表达式包含正确的逻辑
      expect(filterNode.data.config.expression).to.include("col('intent') == 'refund'");
    });
  });
});
