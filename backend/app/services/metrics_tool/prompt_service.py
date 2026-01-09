from app.services.metrics_tool.templates import COT_TEMPLATE_CN, COT_TEMPLATE_EN, COT_TEMPLATE_CN_LITE

def generate_prompt(name, definition, output_format, language="CN", lite_mode=False, aliases="", extraction_mode="Multi"):
    """
    根据用户输入组装最终 Prompt
    """
    # 简单的格式指令映射 (精简指令以节省 token)
    format_map_cn = {
        "JSON": "JSON列表格式 (支持多值): [{\"value\": \"...\", \"unit\": \"...\", \"period\": \"...\", \"source\": \"...\"}, ...]",
        "CSV": "CSV格式 (支持多行): 指标,数值,单位,时间周期,依据",
        "Markdown Table": "Markdown表格 (支持多行): 指标|数值|单位|时间周期|依据"
    }

    format_map_en = {
        "JSON": "JSON List format (Support multiple values): [{\"value\": \"...\", \"unit\": \"...\", \"period\": \"...\", \"source\": \"...\"}, ...]",
        "CSV": "CSV format (Support multiple rows): Indicator,Value,Unit,Period,Source",
        "Markdown Table": "Markdown table (Support multiple rows): Indicator|Value|Unit|Period|Source"
    }
    
    # 确定提取规则文本
    if language == "CN":
        if extraction_mode == "Single":
            extraction_rule_text = "若存在多个符合条件的数据，请仅提取最新或最匹配的一个"
        else:
            extraction_rule_text = "若存在多个符合条件的数据，请全部提取"
    else:
        if extraction_mode == "Single":
            extraction_rule_text = "If multiple matches exist, extract only the single most relevant/recent one"
        else:
            extraction_rule_text = "Extract all values matching the definition (e.g., multiple years/periods)"

    aliases_section = ""
    if aliases and aliases.strip():
        if language == "CN":
            aliases_section = f"\n注意：该指标可能出现在文档中的别名包括：{aliases}。请同时检索这些名称。\n"
        else:
            aliases_section = f"\nNote: The indicator may appear as the following aliases: {aliases}. Please search for these names as well.\n"

    if language == "CN":
        # 如果是 lite 模式，使用极简模板
        template = COT_TEMPLATE_CN_LITE if lite_mode else COT_TEMPLATE_CN
        format_instruction = format_map_cn.get(output_format, format_map_cn["JSON"])
    else:
        template = COT_TEMPLATE_EN
        format_instruction = format_map_en.get(output_format, format_map_en["JSON"])
    
    # 填充模板
    prompt = template.format(
        indicator_name=name,
        aliases_section=aliases_section,
        definition=definition,
        format_instruction=format_instruction,
        extraction_rule_text=extraction_rule_text
    )
    
    return prompt
