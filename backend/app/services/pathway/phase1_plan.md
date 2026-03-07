# Pathway ETL 流水线开发计划 - 阶段 1

## 1. 执行计划

### 1.1 技术方案
本阶段的目标是基于 Pathway 的 `pw.Table` API 构建一个**动态调用工厂 (Dynamic Calling Factory)**。该工厂将作为 ETL 流水线的核心调度单元，负责将字符串形式的算子名称（如 `clean.text_process`, `transform.filter`）映射到具体的 Python 函数或类方法。

**核心组件设计：**

1.  **`OperatorRegistry` (算子注册表)**:
    *   单例模式，维护一个 `name -> function` 的映射字典。
    *   提供 `register(name)` 装饰器，允许在代码中分散注册算子。
    *   提供 `get_operator(name)` 方法，获取算子函数。
    *   支持命名空间（如 `cleaning.uppercase`），便于组织。

2.  **统一算子接口 (Standard Operator Interface)**:
    *   所有算子函数必须遵循统一签名：
        ```python
        def operator_func(table: pw.Table, config: Dict[str, Any]) -> pw.Table:
            ...
        ```
    *   `table`: 输入的 Pathway Table。
    *   `config`: 算子的配置参数字典。
    *   返回值: 转换后的 Pathway Table。

3.  **模块化重构**:
    *   将现有的 `cleaning.py` 和 `udf.py` 中的逻辑适配到新的注册机制。
    *   确保 `engine.py` (执行引擎) 不再硬编码算子逻辑，而是通过工厂调用。

### 1.2 Todo List
- [x] **创建注册中心**: 新建 `backend/app/services/pathway/operators/registry.py`，实现 `OperatorRegistry` 类及装饰器。
- [x] **重构清洗算子**: 修改 `backend/app/services/pathway/operators/cleaning.py`，使用注册装饰器注册现有算子（如 `text_process`, `data_manipulation` 等）。
- [x] **重构 UDF 算子**: 修改 `backend/app/services/pathway/operators/udf.py`，将其注册为标准算子。
- [x] **验证工厂**: 编写单元测试或脚本，验证可以通过字符串名称成功获取并执行算子。
- [x] **集成 (可选)**: 更新 `engine.py` 使用新工厂，实现了统一调用逻辑。

## 2. 测试计划

### 2.1 测试目标与策略
*   **目标**: 验证动态调用工厂能够正确解析算子名称，并正确分发执行逻辑，且不破坏现有功能。
*   **策略**: 采用单元测试为主，集成测试为辅。优先测试核心注册与分发逻辑。

### 2.2 测试范围
*   **功能测试**:
    *   注册功能：验证装饰器是否能将函数注册到字典。
    *   获取功能：验证能否通过名称获取函数。
    *   执行功能：验证获取的函数能否正确处理 `pw.Table`。
    *   异常处理：请求不存在的算子时应抛出明确异常。
*   **兼容性测试**: 确保重构后的 `cleaning.py` 仍能被旧代码（如果有）引用（保持函数名不变，只是增加了装饰器）。

### 2.3 测试环境与数据准备
*   **环境**: 本地开发环境 (Windows), Python 3.x, Pathway 库 (Mock for Windows)。
*   **数据**: 构造简单的 `pw.debug.table_from_markdown` (Mocked) 或内存数据作为输入。

### 2.4 用例设计
| 用例ID | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- |
| TC-01 | 注册与获取 | 无 | 1. 定义新算子并使用 `@register` <br> 2. 调用 `get_operator` | 成功获取函数对象 |
| TC-02 | 文本处理算子调用 | 注册 `text_process` | 1. 工厂获取 `text_process` <br> 2. 传入 Table 和 Config 执行 | Table 字段被正确处理（如转小写） |
| TC-03 | 未知算子报错 | 无 | 1. 调用 `get_operator("unknown")` | 抛出 `OperatorNotFoundError` |
| TC-04 | 重复注册 | 已注册 `op1` | 1. 再次注册同名 `op1` | 覆盖或报错（取决于策略，建议覆盖并打日志） |

### 2.5 测试执行流程
1.  执行 `registry.py` 的单元测试。
2.  执行 `cleaning.py` 的重构后测试。
3.  运行 `python d:\Tiga\backend\app\services\pathway\operators\tests\test_factory.py` (已创建并执行通过)。
