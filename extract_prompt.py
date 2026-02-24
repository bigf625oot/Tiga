import json

def extract_prompt():
    file_path = "d:\\Tiga\\agent_prompt.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompt_text = data["prompt"]
    variables = data["variables"]

    # Substitute variables with defaults
    for var_name, var_info in variables.items():
        value = var_info.get("default", "unknown")
        prompt_text = prompt_text.replace(var_name, str(value))

    print("---EXTRACTED_PROMPT_START---")
    print(prompt_text)
    print("---EXTRACTED_PROMPT_END---")

if __name__ == "__main__":
    extract_prompt()
