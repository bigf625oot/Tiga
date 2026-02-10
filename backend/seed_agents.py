import asyncio
import uuid
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.agent import Agent

# Mock Icons map (since we use frontend components, we can store string identifiers)
# Frontend should map these strings to actual icons
# GlobeAltIcon -> "globe"
# ChartBarIcon -> "chart"
# BookOpenIcon -> "book"
# DocumentTextIcon -> "document"
# PresentationChartLineIcon -> "presentation"
# LightBulbIcon -> "lightbulb"

AGENTS_DATA = [
    {
        "name": "顶层规划",
        "description": "提供战略层面的规划与建议，帮助用户梳理顶层设计思路，涵盖宏观分析与长远布局。",
        "icon": "globe",
        "is_template": True,
        "system_prompt": "你是一个顶层规划专家，擅长宏观战略分析与长远布局...",
    },
    {
        "name": "市场洞察",
        "description": "深入分析市场趋势、竞争格局与用户需求，提供数据驱动的市场洞察报告。",
        "icon": "chart",
        "is_template": True,
        "system_prompt": "你是一个市场分析师，擅长数据挖掘与趋势预测...",
    },
    {
        "name": "专题研究",
        "description": "针对特定主题进行深度挖掘与研究，提供详尽的专题报告与学术支持。",
        "icon": "book",
        "is_template": True,
        "system_prompt": "你是一个资深研究员，擅长深度专题研究...",
    },
    {
        "name": "政策解读",
        "description": "专业解读各类政策文件，分析政策影响与合规要求，提供精准的政策咨询。",
        "icon": "document",
        "is_template": True,
        "system_prompt": "你是一个政策解读专家，擅长法律法规与政策分析...",
    },
    {
        "name": "领导讲话稿",
        "description": "撰写高质量的领导讲话稿，涵盖各类场合与风格，确保语言得体、逻辑严密。",
        "icon": "presentation",
        "is_template": True,
        "system_prompt": "你是一个高级撰稿人，擅长撰写各类领导讲话稿...",
    },
    {
        "name": "解决方案",
        "description": "针对具体业务痛点提供定制化解决方案，结合行业最佳实践，助力问题解决。",
        "icon": "lightbulb",
        "is_template": True,
        "system_prompt": "你是一个解决方案架构师，擅长解决复杂业务问题...",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding agents...")
        for data in AGENTS_DATA:
            # Check if exists by name
            result = await db.execute(select(Agent).where(Agent.name == data["name"]))
            existing = result.scalars().first()
            
            if existing:
                print(f"Agent {data['name']} already exists, updating...")
                existing.description = data["description"]
                existing.icon = data["icon"]
                existing.system_prompt = data["system_prompt"]
                existing.is_template = True
                db.add(existing)
            else:
                print(f"Creating agent {data['name']}...")
                agent = Agent(
                    id=str(uuid.uuid4()),
                    name=data["name"],
                    description=data["description"],
                    icon=data["icon"],
                    is_template=True,
                    system_prompt=data["system_prompt"],
                    model_config={"model_id": "gpt-4o", "reasoning": False},  # Default
                    is_active=True,
                )
                db.add(agent)

        await db.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
