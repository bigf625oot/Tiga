# MinerU 集成实施待办事项 (Todo List)

## 阶段一：POC 验证与环境准备 (POC & Environment Setup)

- [ ] **环境搭建**
    - [ ] 检查服务器 CUDA 驱动版本及兼容性
    - [ ] 安装 `magic-pdf[full]` 及对应版本的 `torch`
    - [ ] 下载 MinerU 所需的模型权重文件 (Layout, OCR, Formula) 并验证完整性
    - [ ] 配置 `magic-pdf.json` 文件指向模型目录

- [ ] **原型验证 (POC)**
    - [ ] 编写独立的 Python 脚本，测试 `magic-pdf` 对本地 PDF 的解析
    - [ ] 选取 5-10 个典型样本文件（包含纯文本、复杂表格、多栏排版、公式）
    - [ ] 对比 MinerU 输出的 Markdown 与原始 PDF 的差异
    - [ ] 记录纯 CPU 与 GPU 环境下的解析耗时

## 阶段二：代码集成开发 (Integration Development)

- [ ] **后端服务开发**
    - [ ] 创建 `backend/app/services/rag/parsers/mineru_parser.py`
    - [ ] 实现 `MinerUParser` 类，封装 `doc_analyze` 调用逻辑
    - [ ] 实现图片提取与存储逻辑（对接对象存储或本地文件系统）
    - [ ] 添加异常捕获机制，确保解析失败时抛出明确错误

- [ ] **异步任务改造**
    - [ ] 检查当前的文档解析是否为异步任务
    - [ ] 如果不是，引入 Celery 或后台任务队列处理 MinerU 解析（因其耗时较长）
    - [ ] 实现进度反馈机制（可选）

- [ ] **配置与开关**
    - [ ] 在 `config.py` 中添加 `ENABLE_MINERU_PARSER` 开关
    - [ ] 在 `config.py` 中添加 MinerU 相关配置（模型路径、GPU ID 等）
    - [ ] 修改 `KnowledgeBaseService`，根据配置选择解析器（MinerU 或 PyMuPDF）

## 阶段三：测试与优化 (Testing & Optimization)

- [ ] **单元测试**
    - [ ] 编写 `tests/test_mineru_parser.py`，模拟 PDF 输入并验证输出格式

- [ ] **性能测试**
    - [ ] 测试大文件（>50页）的解析稳定性
    - [ ] 监控显存占用，防止 OOM (Out of Memory)
    - [ ] 优化并发策略（限制同时进行的 MinerU 任务数量）

- [ ] **回滚与降级**
    - [ ] 实现自动降级逻辑：如果 MinerU 失败或超时，自动切换回 `PyMuPDF`
    - [ ] 记录解析失败的日志以便排查

## 阶段四：部署与文档 (Deployment & Documentation)

- [ ] **部署准备**
    - [ ] 编写 `Dockerfile` 或更新部署脚本，包含 MinerU 依赖
    - [ ] 编写模型下载脚本 `download_models.sh`

- [ ] **文档编写**
    - [ ] 更新项目 `README.md`，说明 MinerU 的启用方法
    - [ ] 编写运维手册，包含常见报错处理

## 阶段五：灰度发布 (Canary Release)

- [ ] **小范围验证**
    - [ ] 在测试环境全量开启
    - [ ] 收集用户反馈和错误日志
    - [ ] 确认无误后在生产环境按需开启
