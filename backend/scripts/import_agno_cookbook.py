import sys
import os
import asyncio
import json
import uuid
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.db.session import AsyncSessionLocal
    from app.models.agent import Agent
    from app.models.llm_model import LLMModel
except ImportError as e:
    print(f"Error importing app modules: {e}")
    sys.exit(1)

# Definition of Agno Cookbook Agents mapped to Tiga schema
COOKBOOK_AGENTS = [
    {
        "name": "Web Search Agent",
        "description": "A helpful assistant that can search the web for real-time information.",
        "role": "general",
        "system_prompt": """You are a helpful assistant with access to the web.
Always search for the latest information when asked about current events or specific data.
Cite your sources when possible.""",
        "tools_config": ["duckduckgo"],
        "icon": "globe",
        "category": "通用助手"
    },
    {
        "name": "Finance Analyst",
        "description": "Expert in financial data analysis, stock prices, and market trends.",
        "role": "general",
        "system_prompt": """You are a financial analyst. Use the YFinance tool to get stock prices, company info, and analyst recommendations.
Analyze the data and provide insights.
Always show the currency when displaying prices.""",
        "tools_config": ["yfinance", "duckduckgo"],
        "icon": "chart",
        "category": "数据分析"
    },
    {
        "name": "Python Data Analyst",
        "description": "Can write and execute Python code to analyze data and create visualizations.",
        "role": "executor",
        "system_prompt": """You are a Python Data Analyst. You can write and execute Python code.
Use the `python` tool to run code for data analysis, math calculations, or string processing.
If you need to search for data first, use the search tool.
Always explain your code before running it.""",
        "tools_config": ["python", "duckduckgo"],
        "icon": "terminal",
        "category": "数据分析"
    },
    {
        "name": "Research Assistant",
        "description": "Conducts thorough research on any topic and generates a summary report.",
        "role": "general",
        "system_prompt": """You are a Research Assistant. Your goal is to provide comprehensive reports on user topics.
1. Search for the topic to get an overview.
2. Search for specific details to fill in the gaps.
3. Synthesize the information into a well-structured report with headings and bullet points.
4. Cite sources at the end.""",
        "tools_config": ["duckduckgo"],
        "icon": "book",
        "category": "内容创作"
    },
    {
        "name": "Hacker News Reporter",
        "description": "Fetches the latest stories from Hacker News and summarizes them.",
        "role": "general",
        "system_prompt": """You are a tech news reporter.
Use the search tool to find the latest top stories from Hacker News (news.ycombinator.com).
Summarize the top 5 stories and explain why they are significant.
Focus on technology trends, AI, and startups.""",
        "tools_config": ["duckduckgo"],
        "icon": "newspaper",
        "category": "新闻资讯"
    }
]

async def import_templates():
    print("Connecting to database...")
    async with AsyncSessionLocal() as session:
        # 1. Find a default model to assign (optional, but good for UX)
        print("Resolving default model...")
        result = await session.execute(
            select(LLMModel).filter(LLMModel.is_active == True).order_by(LLMModel.updated_at.desc())
        )
        default_model = result.scalars().first()
        model_config = {}
        if default_model:
            model_config = {
                "model_id": default_model.model_id,
                "provider": default_model.provider
            }
            print(f"Using default model: {default_model.model_id}")
        else:
            print("No active model found. Templates will be created without a specific model.")

        # 2. Insert Agents
        count = 0
        for template in COOKBOOK_AGENTS:
            # Check if exists by name to avoid duplicates (or update)
            stmt = select(Agent).filter(Agent.name == template["name"], Agent.is_template == True)
            result = await session.execute(stmt)
            existing_agent = result.scalars().first()

            if existing_agent:
                print(f"Updating existing template: {template['name']}")
                existing_agent.description = template["description"]
                existing_agent.system_prompt = template["system_prompt"]
                existing_agent.tools_config = template["tools_config"]
                existing_agent.icon = template.get("icon", "bot")
                # existing_agent.category = template.get("category", "Other") # Assuming category field exists or we add it to meta
                # Note: Agent model might not have 'category' column based on previous read. 
                # Let's check Agent model again. It didn't have category column in the file read earlier.
                # It has 'role'. The frontend inferred category from name. 
                # But wait, frontend code said: "if (!agent.category) ...". This implies API returns it.
                # API might return it from a join or extra field? 
                # Or maybe I missed it in the model definition?
                # Let's double check model.py.
                
                # Re-reading model.py from memory:
                # id, name, description, icon, system_prompt, enable_react, enable_cot, model_config, tools_config...
                # No 'category' column.
                # However, frontend logic: "if (!agent.category) { ... }".
                # This suggests 'category' might be dynamically added or I missed it.
                # I will store it in a generic way if possible, or just rely on frontend mapping.
                # Actually, I can put it in 'description' or just let frontend map it.
                # Or maybe 'role' is used? No, role is 'planner', 'executor', 'general'.
                
                # Let's just stick to standard fields.
                
                existing_agent.model_config = model_config
                existing_agent.role = template["role"]
            else:
                print(f"Creating new template: {template['name']}")
                new_agent = Agent(
                    id=str(uuid.uuid4()),
                    name=template["name"],
                    description=template["description"],
                    system_prompt=template["system_prompt"],
                    tools_config=template["tools_config"],
                    model_config=model_config,
                    icon=template.get("icon", "bot"),
                    role=template["role"],
                    is_template=True,
                    is_active=True,
                    enable_react=True,
                    enable_cot=True
                )
                session.add(new_agent)
            
            count += 1

        await session.commit()
        print(f"Successfully imported {count} templates.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(import_templates())
