# Taichi Agent Prompt Template

## Overview
This document describes the `agent_prompt.json` template, which serves as the core configuration for the Taichi Agent. This template is designed to ensure functional completeness, tool compatibility, context consistency, extensibility, security, and performance.

## Structure

The `agent_prompt.json` file is structured as follows:

-   **`prompt`**: The base prompt text defining the agent's persona, capabilities, and constraints.
-   **`variables`**: Project-level variables (e.g., `${project_name}`, `${version}`) used for dynamic substitution.
-   **`tools`**: A list of available tools, their descriptions, and parameter schemas.
-   **`extensions`**: Schema for dynamically injecting new capabilities.
-   **`test_cases`**: Sample inputs and expected behaviors for testing.
-   **`metrics`**: SLA and monitoring thresholds.

## Knowledge Base Capabilities

The agent now includes enhanced knowledge base retrieval features:

1.  **Multi-Source Retrieval**: Queries Sandbox logs, Local Files, Git Repos, API Docs, and History.
2.  **Smart Triggers**: Automatically activates on keywords like "how to", "example", etc.
3.  **Dynamic Updates**: Syncs data hourly.
4.  **Privacy**: Filters sensitive data from sandbox logs.

### Configuration Example

To enable specific knowledge sources, update the `knowledge_base_tools` configuration in `agent_prompt.json`:

```json
{
  "name": "search_knowledge_base",
  "parameters": {
    "sources": ["sandbox", "git", "api_docs"]
  }
}
```

## Usage

### 1. Initialization

Load the `agent_prompt.json` file and substitute variables:

```python
import json
import os

def load_prompt(file_path="agent_prompt.json"):
    with open(file_path, "r") as f:
        data = json.load(f)

    prompt_text = data["prompt"]
    variables = data["variables"]

    # Substitute variables
    for var_name, var_info in variables.items():
        value = os.getenv(var_name.strip("${}"), var_info["default"])
        prompt_text = prompt_text.replace(var_name, value)

    return prompt_text, data["tools"]

prompt, tools = load_prompt()
print(prompt)
```

### 2. Extending Capabilities

To add new tools without modifying the core template, define extensions in a separate file (e.g., `extensions.json`) following the `extensions.validation_schema`.

### 3. Monitoring & Security

-   **Trace ID**: Automatically generated for each request and included in logs.
-   **Audit Logs**: All tool executions are logged.
-   **Performance**: Operations taking >500ms will be flagged with the Trace ID.

## Testing

Run the included test script to validate the prompt template:

```bash
python tests/test_agent_prompt.py
```

## Contributing

1.  Modify `agent_prompt.json` to update the prompt or tools.
2.  Add new test cases to `test_cases` array.
3.  Ensure JSON validity and schema compliance.
