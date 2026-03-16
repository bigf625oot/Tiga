Plan Agent (Solo 模式) 系统化调试测试用例集
第一部分：规划逻辑层 (Planning & Reasoning Layer)
调试重点：验证 LLM 的逻辑分解能力与 Agno 框架 reasoning 字段的提取。
TC-PL-01: 复杂逻辑依赖与分解
测试场景：测试 Agent 是否理解任务的先后物理顺序（A 必须在 B 前）。
输入指令：“先帮我生成一个 5x5 的随机整数矩阵并存入 matrix.json，然后读取该文件计算每一行的平均值，最后将平均值存为 Result.txt。”
系统化调试路径：
Backend (Agno)：检查 plan_steps 是否被拆分为至少 3 个 Step，且第 2 步的描述中明确包含对 matrix.json 的引用。
Reasoning Log：观察是否输出了“我需要先创建文件，因为后续步骤依赖它”的逻辑。
Frontend：右侧 Plan Tab 必须在 T0 秒内渲染出完整的 3 个 Pending 步骤。
观测指标：reasoning_path_correctness (Binary), step_granularity (Steps >= 3)。
TC-PL-02: 模糊指令的确定性转化
测试场景：测试 Agent 在面对不具体指令时的“默认决策”能力。
输入指令：“分析一下最近三天的天气对上海旅游的影响。”
系统化调试路径：
Tool Selection：Agent 是否自动触发了 Web Search？
Dynamic Expansion：计划是否包含了“1. 搜索天气”、“2. 搜索旅游热点”、“3. 综合建模”？
观测指标：implicit_goal_extraction (是否识别出需要搜索)。
第二部分：工具执行与数据流转层 (Tool & Data Flow Layer)
调试重点：验证结构化数据在各工具与 Python 环境间的传递。
TC-TD-01: 跨工具长链路闭环 (Search -> Python -> File)
测试场景：测试搜索引擎返回的大量文本能否被 Python 正确截断或解析。
输入指令：“搜索 2024 年全球市值前五的科技公司，提取它们的名称和市值数值，用 Python 画一个饼图存为 market_cap.png。”
系统化调试路径：
Tool Response：观察 Search 返回的 JSON 是否包含非 UTF-8 字符导致 Python 调用失败。
Payload Transfer：检查 LLM 传递给 Python 工具的代码中，硬编码的数值是否与搜索结果一致。
Sandbox：检查 market_cap.png 的生成路径是否在 /workspace。
观测指标：data_transfer_fidelity (搜索结果与代码参数的一致性)。
TC-TD-02: 大规模数据 I/O 压力
测试场景：测试 Agent 处理超长 Stdout 输出时的流式性能。
输入指令：“用 Python 生成一个包含 5000 行记录的 CSV，每行随机生成姓名和日期，并打印前 100 行。”
系统化调试路径：
Stream Lag：前端 Console Tab 是否因为 5000 行输出导致卡顿？
Truncation：Agno 是否对过长的输出进行了截断以防止上下文溢出（Token Limit）？
观测指标：stdout_streaming_latency, token_usage_protection。
第三部分：闭环自愈与健壮性层 (Self-Healing Layer)
调试重点：通过构造“必然失败”的中间环节，测试 Agent 的 Reflection 机制。
TC-SH-01: Python 语法与逻辑自修复
测试场景：测试代码报错后的自我迭代。
输入指令：“用 Python 读取一个不存在的文件 dummy.txt。如果报错，请生成该文件并随便写点内容，然后再尝试读取。”
系统化调试路径：
First Failure：记录第一次 code_exec 返回的 FileNotFoundError。
Reasoning Change：观察 Agent 是否输出“检测到文件缺失，正在执行生成补偿步骤”。
Loop Closure：最终是否输出了读取成功的内容。
观测指标：healing_iterations (预期 2 次), error_context_understanding。
TC-SH-02: 搜索结果无效时的动态调优
测试场景：测试搜索无果时的策略变更。
输入指令：“查询一个不存在的虚构角色‘张三丰在 2025 年获得的诺贝尔奖’，并给出详细解释。”
系统化调试路径：
Search Feedback：搜索返回空或无关结果。
Strategy Pivot：Agent 是直接撒谎，还是推理出“2025 年尚未到来或该人物为虚构”，转而搜索“2025 年预测”或确认事实？
观测指标：hallucination_prevention (是否能拒绝幻觉并修正路线)。
第四部分：UI 状态同步与持久化 (UI & State Layer)
调试重点：前端 Workspace 与后端 Agent 状态的原子性。
TC-UI-01: 实时状态机同步
测试场景：高频状态更新。
输入指令：“执行一个 10 步的计划，每步只是简单的 print('step X')，每步间隔 1 秒。”
系统化调试路径：
Frontend Rendering：右侧 Plan Tab 的 Checkmark 状态是否与 Console 的输出同步？
Protocol Trace：检查 WebSocket/SSE 消息中的 status_update 包是否丢失。
观测指标：ui_sync_delay (< 500ms)。
5. Systematic Debugging 故障诊断矩阵 (Diagnostic Matrix)
在使用上述用例时，若发生失败，请参照下表定位：
故障现象	潜在根本原因 (Root Cause)	检查位置
计划卡住，步骤不更新	Agno plan_step 信号未通过 Socket 发送或前端逻辑死锁	Network Tab -> WS Frames
生成的图表显示不出来	文件生成路径与前端 Static 目录映射错误；Base64 转换失败	/workspace 目录与 API Response
Agent 反复执行同一代码	Reasoning 循环（没有更新提示词来意识到已执行过）	Backend Prompt Logs
搜索结果与报告内容无关	搜索结果过长导致上下文截断，丢弃了关键信息	LLM Input Context
Console 报错但 Plan 显示勾选	状态更新逻辑只检查了“执行动作”，没检查“执行结果成功”	Python Tool Wrapper Return Code
6. 测试执行建议
开启 Debug 模式：启动 Agno 时，强制输出 agent.print_response=True。
沙箱快照：在每个 TC 执行前后，执行 ls -R /workspace 记录文件系统状态。
时间戳对比：记录后端发送 tool_call 与前端收到 tool_result 的 Unix 时间戳差值。