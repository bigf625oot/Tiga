# 交互设计 (Interaction Design)

## 1. 用户旅程图 (User Journey Map)

```mermaid
journey
    title ETL 流水线构建旅程
    section 1. 创建 (Creation)
      新建流水线: 5: 用户
      选择模板 (可选): 3: 用户
      初始化画布: 5: 系统
    section 2. 配置 (Configuration)
      拖拽数据源节点: 5: 用户
      配置连接参数: 4: 用户
      拖拽转换节点: 5: 用户
      连接节点: 5: 用户
      配置转换逻辑: 3: 用户
      拖拽输出节点: 5: 用户
      配置目标库: 4: 用户
    section 3. 验证 (Validation)
      点击"校验": 5: 用户
      静态检查配置: 5: 系统
      显示错误提示 (如有): 4: 系统
      点击"预览数据": 4: 用户
      展示采样数据: 5: 系统
    section 4. 运行 (Execution)
      点击"发布/运行": 5: 用户
      提交任务至后端: 5: 系统
      显示"启动中": 5: 系统
      流转为"运行中": 5: 系统
    section 5. 监控 (Monitoring)
      查看实时指标: 4: 用户
      查看日志: 3: 用户
      处理异常 (如有): 2: 用户
```

## 2. 节点状态机 (Node State Machine)

```mermaid
stateDiagram-v2
    [*] --> Idle: 拖入画布
    
    Idle --> ConfigIncomplete: 缺少必填参
    ConfigIncomplete --> Idle: 补全参数
    
    Idle --> Validating: 点击校验/自动校验
    Validating --> ConfigError: 校验失败
    ConfigError --> Idle: 修改配置
    
    Validating --> Ready: 校验通过
    
    Ready --> Starting: 点击运行
    Starting --> Running: 后端进程启动
    
    Running --> Error: 运行时异常
    Error --> Running: 自动重试
    Error --> Stopped: 重试失败/手动停止
    
    Running --> Stopped: 手动停止
    Stopped --> Starting: 重新运行
    
    note right of Idle
      灰色边框
      无状态图标
    end note
    
    note right of Running
      绿色呼吸边框
      Loading/Spinner图标
      显示速率指标
    end note
    
    note right of Error
      红色边框
      警告图标
      Tooltip显示错误信息
    end note
```

## 3. 交互细节说明

### 画布操作
- **拖拽 (Drag & Drop)**: 左侧组件库 -> 画布。
- **连接 (Connect)**: 节点右侧锚点 -> 目标节点左侧锚点。
- **框选 (Selection)**: 按住鼠标左键拖动框选多个节点。
- **快捷键**:
    - `Ctrl + S`: 保存
    - `Ctrl + Z`: 撤销
    - `Delete / Backspace`: 删除选中节点/连线
    - `Space + Drag`: 拖动画布

### 节点反馈
- **Hover**: 显示简要信息（类型、名称）。
- **Selected**: 蓝色高亮边框，右侧展开属性面板。
- **Running**: 节点右上角显示绿色状态点，连接线上显示流动动画。
- **Error**: 节点变红，点击显示错误详情 Modal。

### 属性面板 (右侧)
- **动态表单**: 根据节点类型渲染不同配置项。
- **即时校验**: 输入框失去焦点时进行格式校验。
- **代码编辑**: 对于 UDF 节点，提供嵌入式 Monaco Editor。
