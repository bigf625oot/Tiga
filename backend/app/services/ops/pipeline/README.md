# Pathway 数据集成服务

本服务提供基于 [Pathway](https://pathway.com/) 的统一数据集成解决方案，无缝集成到后端架构中。

## 核心特性

- **统一架构**：复用现有的依赖注入、配置管理、日志记录和错误处理机制，无需独立部署服务。
- **多源接入**：支持 Kafka、结构化数据库（通过 Debezium/JDBC 连接 Postgres/MySQL）、S3 对象存储、REST API 等多种数据源。
- **数据清洗**：内置丰富的算子库，覆盖文本处理、数据操作、列表处理和聚合统计四大类场景。
- **用户自定义函数 (UDF)**：支持动态加载 Python 脚本，实现复杂的自定义转换逻辑。
- **多端输出**：
    - **OLAP**: ClickHouse
    - **缓存**: Redis
    - **搜索**: Elasticsearch
    - **图数据库**: Neo4j (支持节点/关系 MERGE)
    - **知识图谱存储**: LightRAG (JSON/GraphML 分片存储)
    - **向量与对象存储**: Vector DB (FAISS/PGVector) + MinIO/S3
- **实时处理**：端到端延迟低于 3 秒，满足高时效性业务需求。
- **监控告警**：暴露 Prometheus 格式指标 (`/metrics/prometheus`)，便于 Grafana 集成展示。

## 目录结构

```
backend/app/services/pathway/
├── core/           # 引擎封装与配置管理
├── operators/      # 数据清洗与转换算子库
├── connectors/     # 数据源与目标连接器
│   ├── base.py
│   ├── source.py
│   ├── sink.py
│   └── persistence.py # 高级持久化连接器 (Neo4j, LightRAG, Vector)
├── api/            # FastAPI 路由（任务控制）
├── scripts/        # 运行脚本
├── tests/          # 单元测试与集成测试
└── README.md       # 本文档
```

## 算子库详解

本服务内置了四大类清洗算子，通过 `type` 字段指定大类，`action` 字段指定具体操作。

### 1. 文本处理 (`type: text_process`)

用于处理字符串类型的字段。

| Action | 描述 | 参数 (`params`) |
| :--- | :--- | :--- |
| `case_convert` | 大小写转换 | `mode`: "lower" (小写), "upper" (大写), "title" (标题化) |
| `width_convert` | 全角转半角 | 无 |
| `emoji_clean` | Emoji 清除/替换 | `mode`: "remove" (清除) 或 "replace" (替换); `replace_str`: 替换字符 |
| `regex` | 正则替换或提取 | `pattern`: 正则表达式; `repl`: 替换串; `method`: "replace" 或 "extract" |
| `tokenize` | 分词 | `engine`: "split" (空格切分) 或 "jieba" (结巴分词) |
| `stem` | 词干提取 | 无 (使用 PorterStemmer) |
| `keyword_extract` | 关键词提取 | `top_k`: 提取数量 (基于 TF-IDF) |
| `sensitive_filter` | 敏感词过滤 | `words`: 敏感词列表; `replace_char`: 掩码字符 |
| `similarity` | 字符串相似度 | `col1`, `col2`: 比较列; `out_col`: 输出列; `method`: "ratio" |

### 2. 数据操作 (`type: data_manipulation`)

用于数值计算、类型转换和缺失值处理。

| Action | 描述 | 参数 (`params`) |
| :--- | :--- | :--- |
| `missing` | 缺失值填充 | `strategy`: "constant" (常量); `value`: 填充值 |
| `cast` | 类型转换 | 在 `columns` 中指定目标类型 ("int", "float", "str", "bool") |
| `math` | 数学运算 | `operation`: 如 "c_to_f" (摄氏转华氏), "f_to_c" |
| `sampling` | 随机采样 | `rate`: 采样率 (0.0-1.0); `key_col`: 用于哈希的键列 |
| `outlier_zscore` | Z-Score 异常检测 | `mean`: 均值; `std`: 标准差; `threshold`: 阈值 |
| `unit_convert` | 单位换算 | `factor`: 乘数; `offset`: 偏移量 |

### 3. 列表操作 (`type: list_operation`)

用于处理数组/列表类型的字段。

| Action | 描述 | 参数 (`params`) |
| :--- | :--- | :--- |
| `deduplication` | 列表去重 | 无 |
| `sort` | 列表排序 | `reverse`: 是否倒序 (true/false) |
| `flatten` | 列表扁平化 | 无 (将嵌套列表展开) |
| `frequency` | 元素频次统计 | 无 (返回字典 `{元素: 计数}`) |
| `set_ops` | 集合运算 | `method`: "intersection" (交), "union" (并), "difference" (差); `col1`, `col2`, `out_col` |
| `json_parse` | JSON 解析 | 无 (字符串 -> 对象/列表) |

### 4. 变量聚合 (`type: variable_aggregation`)

用于分组统计和聚合。

| Action | 描述 | 配置 (`config`) |
| :--- | :--- | :--- |
| `groupby` | 分组聚合 | `group_by`: 分组列名列表; `aggregations`: 聚合配置 |

**聚合配置示例 (`aggregations`)**:
```yaml
total_amount:
  col: amount
  func: sum  # 支持: sum, count, avg, min, max, hll (基数估计)
```

## 配置指南

服务通过 `pathway.yml` 进行声明式配置。

### 完整配置示例

```yaml
# 任务名称
name: "user_behavior_analytics"

# 数据源配置
sources:
  - type: kafka
    config:
      topic: "app_events"
      bootstrap_servers: "kafka:9092"
      format: "json"
      columns:
        user_id: str
        event_type: str
        timestamp: int
        payload: str  # JSON string

# 算子链配置
operators:
  # 1. 解析 Payload JSON
  - type: list_operation
    config:
      action: json_parse
      columns:
        payload_obj: payload

  # 2. 文本标准化
  - type: text_process
    config:
      action: case_convert
      columns: ["event_type"]
      params:
        mode: "upper"

  # 3. 缺失值填充
  - type: data_manipulation
    config:
      action: missing
      columns: ["user_id"]
      params:
        strategy: "constant"
        value: "anonymous"

  # 4. 敏感词过滤 (UDF 示例，这里使用内置算子)
  - type: text_process
    config:
      action: sensitive_filter
      columns: ["payload_obj"]
      params:
        words: ["admin", "root"]
        replace_char: "*"

# 输出端配置
sinks:
  - type: clickhouse
    config:
      host: "clickhouse"
      port: 8123
      database: "analytics"
      table: "events_clean"
      columns: ["user_id", "event_type", "timestamp", "payload_obj"]

  - type: redis
    config:
      host: "redis"
      port: 6379
      key_column: "user_id"
      value_column: "event_type"

# 全局设置
settings:
  monitoring_port: 8081
```

## 开发与运行

### 1. 安装依赖

```bash
pip install -r backend/app/services/pathway/requirements-pathway.txt
```

### 2. 本地启动

服务已集成到主应用中，启动 FastAPI 即可：

```bash
uvicorn app.main:app --reload
```

### 3. API 接口

| 方法 | 路径 | 描述 |
| :--- | :--- | :--- |
| POST | `/api/v1/pathway/jobs` | 提交并启动一个新的集成任务 |
| GET | `/api/v1/pathway/jobs/{name}` | 查询任务状态 |
| DELETE | `/api/v1/pathway/jobs/{name}` | 停止任务 |
| GET | `/metrics/prometheus` | 获取监控指标 |

## 测试

本项目包含完善的单元测试和集成测试。

运行所有测试：
```bash
pytest backend/app/services/pathway/tests
```

运行特定测试文件：
```bash
pytest backend/app/services/pathway/tests/test_operators.py
pytest backend/app/services/pathway/tests/test_persistence.py
```

## 高级持久化脚本

使用 `scripts/persistence_runner.py` 运行端到端的高级持久化测试（Neo4j, LightRAG, Vector）：

```bash
python backend/app/services/pathway/scripts/persistence_runner.py
```
