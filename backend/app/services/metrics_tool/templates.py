# 极简版中文模板 (Token Optimized)
COT_TEMPLATE_CN_LITE = """
# Task
根据 # Definition 提供的定义，从 # Text 部分的文本中提取或计算指标：“{indicator_name}”。
{aliases_section}
# Definition
{definition}

# Rules
1. 提取符合定义的数值。{extraction_rule_text}。若无匹配数据，JSON格式请返回空列表 []，其他格式返回 "N/A"。
2. 严格检查单位和时间周期 (Period)。
3. 按此格式输出：{format_instruction}

# Text
{{text_content}}
"""

# 标准版中文 CoT 模板 (High Accuracy)
COT_TEMPLATE_CN = """
# Role
你是一位数据提取专家。任务是根据 # Definition 提供的定义，从 # Text 中提取或计算指标：“{indicator_name}”。
{aliases_section}
# Definition
{definition}

# Steps
1. **定位**: 寻找与指标相关的关键词及数值。
2. **验证**: 确认数值的单位和口径符合定义（{extraction_rule_text}）。
3. **输出**: 输出包含所有提取结果的列表（若无数据，JSON格式返回 []，其他格式返回 "N/A"）。

# Format
{format_instruction}

# Text
{{text_content}}
"""

# 英文版同理优化
COT_TEMPLATE_EN = """
# Task
Extract the indicator "{indicator_name}" from the text below.
{aliases_section}
# Definition
{definition}

# Rules
1. Extract values matching the definition. {extraction_rule_text}. If none found, return empty list [] for JSON, or "N/A" for others.
2. Verify units and time period.
3. Output format: {format_instruction}

# Text
{{text_content}}
"""
