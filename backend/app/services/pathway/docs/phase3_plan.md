# Pathway ETL 流水线开发计划 - 阶段 3 (DAG 解析器)

## 1. 执行计划

### 1.1 技术方案
本阶段的目标是实现一个基于 DAG (有向无环图) 的解析器，能够将前端定义的复杂节点连接关系解析为可执行的 Pathway 计算图。这将替代目前简单的线性 (Source -> Operators -> Sink) 执行模式。

**核心组件设计：**

1.  **DAG 数据模型 (Pydantic Models)**:
    *   定义 `DAGNode` 和 `DAGPipeline` 模型，支持多输入、多输出及分支合并。
    *   `DAGNode` 包含 `id`, `type` (source/transform/sink), `operator` (具体算子名), `config` (参数), `inputs` (依赖的节点ID列表)。

2.  **节点工厂 (Node Factory)**:
    *   `NodeFactory` 类负责根据节点类型和配置实例化具体的 Pathway Table 对象。
    *   利用 Phase 1 的 `OperatorRegistry` 和 Phase 2 的 `DataSourceBridge`。

3.  **DAG 解析器 (DAGParser)**:
    *   **拓扑排序**: 解析节点依赖关系，确定执行顺序。
    *   **构建计算图**: 按顺序遍历节点，将上游节点的输出 Table 作为下游节点的输入。
    *   **参数校验**: 检查必填参数和类型匹配。

4.  **引擎升级**:
    *   更新 `PathwayEngine` 以支持新的 `DAGPipeline` 配置格式。

### 1.2 Todo List
- [x] **定义 DAG 模型**: 创建 `backend/app/services/pathway/core/models.py`，定义 `DAGNode`, `DAGPipeline` 等 Pydantic 模型。
- [x] **实现 DAG 解析器**: 创建 `backend/app/services/pathway/core/parser.py`，实现 `DAGParser` 类，包含拓扑排序和图构建逻辑。
- [x] **更新执行引擎**: 修改 `backend/app/services/pathway/core/engine.py`，使其能够接收并执行 DAG 配置。
- [x] **编写测试用例**: 创建 `backend/app/services/pathway/core/tests/test_parser.py`，验证复杂 DAG (如分支、合并) 的解析与执行。

## 2. 测试计划

### 2.1 测试目标
验证解析器能够正确处理复杂的节点依赖关系，并生成正确的 Pathway 计算图。

### 2.2 测试范围
*   **线性流**: Source -> Transform -> Sink (回归测试)。
*   **分支流**: Source -> Transform A & Transform B (由一个源分发给两个处理)。
*   **合并流**: Source A & Source B -> Join/Union -> Sink。
*   **异常处理**: 循环依赖检测、孤立节点检测、无效的算子名称。

### 2.3 测试环境
*   使用 Mock 的 Pathway 对象进行单元测试，避免启动真实的 Pathway 引擎进程。
*   利用 `pw.debug.table_from_markdown` 模拟数据源。

### 2.4 用例设计
| 用例ID | 用例名称 | 描述 | 预期结果 |
| :--- | :--- | :--- | :--- |
| TC-DAG-01 | 线性流水线 | 简单的 A->B->C 结构 | 成功构建，C 的输入是 B，B 的输入是 A |
| TC-DAG-02 | 多源合并 | A, B -> Union -> C | C 的输入包含 A 和 B 的 Table |
| TC-DAG-03 | 循环依赖检测 | A->B->A | 抛出 `CycleError` 或解析失败 |
| TC-DAG-04 | 参数校验 | 节点配置缺失必填项 | 抛出 `ValidationError` |

### 2.5 测试执行结果
*   所有单元测试通过。验证了线性流、Union合并流、循环依赖检测和缺失输入检测。
