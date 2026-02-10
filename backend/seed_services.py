import asyncio
import uuid
from sqlalchemy import select, update

from app.db.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.mcp import MCPServer
from app.core.logger import logger

SKILLS_DATA = [
    {
        "name": "Code Reviewer",
        "description": "检查代码补丁中的错误、风格问题和安全漏洞。提供建设性的反馈。",
        "content": """# Code Reviewer Skill
## Role
You are a senior software engineer conducting a code review.

## Instructions
1. Analyze the provided code diff or snippet.
2. Identify potential bugs, logic errors, and security vulnerabilities.
3. Suggest improvements for code style, readability, and performance.
4. Provide code snippets for your suggestions.
5. Be constructive and professional.

## Input
Code diff or file content.

## Output
Markdown formatted review report.
""",
        "category": "dev-tools",
        "author": "Tiga Team",
        "version": "1.0.0",
        "is_official": True
    },
    {
        "name": "Git Helper",
        "description": "帮助处理复杂的 git 命令和工作流程。可以生成提交信息并解释 git 概念。",
        "content": """# Git Helper Skill
## Role
You are a Git expert.

## Instructions
1. Explain complex git commands (rebase, cherry-pick, bisect) in simple terms.
2. Generate semantic commit messages based on staged changes.
3. Help resolve merge conflicts by analyzing conflict markers.
4. Suggest git workflows for specific team scenarios.

## Input
User question about git or git status output.
""",
        "category": "dev-tools",
        "author": "Tiga Team",
        "version": "1.1.0",
        "is_official": True
    },
    {
        "name": "SQL Optimizer",
        "description": "分析 SQL 查询并建议优化以提高性能。",
        "content": """# SQL Optimizer Skill
## Role
You are a Database Administrator and SQL Expert.

## Instructions
1. Analyze the given SQL query for performance bottlenecks.
2. Suggest indexing strategies.
3. Rewrite the query to be more efficient if possible.
4. Explain the execution plan if provided.

## Input
SQL query and optional schema/execution plan.
""",
        "category": "data",
        "author": "Data Team",
        "version": "1.0.0",
        "is_official": True
    },
    {
        "name": "Regex Generator",
        "description": "根据自然语言描述生成并解释正则表达式。",
        "content": """# Regex Generator Skill
## Role
You are a Regular Expression expert.

## Instructions
1. Translate the user's natural language requirement into a Regular Expression (Regex).
2. Explain each part of the generated Regex.
3. Provide examples of strings that match and do not match.
4. Support Python, JavaScript, and Go regex flavors.

## Input
Description of the pattern to match.
""",
        "category": "dev-tools",
        "author": "Community",
        "version": "0.9.0",
        "is_official": False
    },
    {
        "name": "Doc Writer",
        "description": "从代码生成全面的文档，包括文档字符串和 README。",
        "content": """# Doc Writer Skill
## Role
You are a Technical Writer.

## Instructions
1. Read the provided code.
2. Generate clear and concise docstrings for functions and classes.
3. Create a README.md file summarizing the project or module.
4. Include usage examples.

## Input
Source code file(s).
""",
        "category": "productivity",
        "author": "Tiga Team",
        "version": "1.2.0",
        "is_official": True
    }
]

MCP_DATA = [
    {
        "name": "Filesystem",
        "description": "安全访问本地文件系统以读取和写入文件。",
        "type": "stdio",
        "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]},
        "category": "system",
        "author": "Model Context Protocol",
        "version": "1.0.0",
        "is_official": True
    },
    {
        "name": "GitHub",
        "description": "与 GitHub API 集成，以管理存储库、议题和 PR。",
        "type": "stdio",
        "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": {"GITHUB_TOKEN": "YOUR_TOKEN_HERE"}},
        "category": "dev-tools",
        "author": "Model Context Protocol",
        "version": "1.0.0",
        "is_official": True
    },
    {
        "name": "PostgreSQL",
        "description": "对 PostgreSQL 数据库的只读或读写访问。",
        "type": "stdio",
        "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:password@localhost/db"]},
        "category": "data",
        "author": "Model Context Protocol",
        "version": "1.0.0",
        "is_official": True
    },
    {
        "name": "Brave Search",
        "description": "使用 Brave Search API 执行网络搜索。",
        "type": "stdio",
        "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": {"BRAVE_API_KEY": "YOUR_KEY_HERE"}},
        "category": "search",
        "author": "Brave",
        "version": "1.0.0",
        "is_official": True
    },
    {
        "name": "Google Maps",
        "description": "访问位置数据、地点和方向。",
        "type": "stdio",
        "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-google-maps"], "env": {"GOOGLE_MAPS_API_KEY": "YOUR_KEY_HERE"}},
        "category": "utility",
        "author": "Google",
        "version": "1.0.0",
        "is_official": False
    },
    {
        "name": "Memory",
        "description": "代理的持久知识图谱记忆。",
        "type": "stdio",
        "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]},
        "category": "system",
        "author": "Model Context Protocol",
        "version": "1.0.0",
        "is_official": True
    }
]

async def seed():
    async with AsyncSessionLocal() as db:
        logger.info("Seeding Skills...")
        for data in SKILLS_DATA:
            # Check existence by name to avoid dupes
            result = await db.execute(select(Skill).where(Skill.name == data["name"]))
            existing = result.scalars().first()
            if not existing:
                logger.info(f"Adding Skill: {data['name']}")
                skill = Skill(
                    id=str(uuid.uuid4()),
                    name=data["name"],
                    description=data["description"],
                    content=data["content"],
                    category=data["category"],
                    author=data["author"],
                    version=data["version"],
                    is_official=data["is_official"],
                    is_active=True
                )
                db.add(skill)
            else:
                logger.info(f"Updating existing Skill: {data['name']}")
                existing.description = data["description"]
                existing.content = data["content"]
                existing.category = data["category"]
                existing.author = data["author"]
                existing.version = data["version"]
                existing.is_official = data["is_official"]
                db.add(existing) # Re-add to session to ensure update is tracked (though usually auto-tracked)
        
        logger.info("Seeding MCP Servers...")
        for data in MCP_DATA:
             # Check existence by name
            result = await db.execute(select(MCPServer).where(MCPServer.name == data["name"]))
            existing = result.scalars().first()
            if not existing:
                logger.info(f"Adding MCP: {data['name']}")
                mcp = MCPServer(
                    id=str(uuid.uuid4()),
                    name=data["name"],
                    description=data["description"],
                    type=data["type"],
                    config=data["config"],
                    category=data["category"],
                    author=data["author"],
                    version=data["version"],
                    is_official=data["is_official"],
                    is_active=True
                )
                db.add(mcp)
            else:
                logger.info(f"Updating existing MCP: {data['name']}")
                existing.description = data["description"]
                existing.type = data["type"]
                existing.config = data["config"]
                existing.category = data["category"]
                existing.author = data["author"]
                existing.version = data["version"]
                existing.is_official = data["is_official"]
                db.add(existing)

        await db.commit()
        logger.info("Seeding Completed!")

if __name__ == "__main__":
    asyncio.run(seed())
