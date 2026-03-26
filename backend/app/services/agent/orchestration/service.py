import logging
from typing import List, Sequence
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, ServiceException
from app.core.i18n import _
from app.crud.crud_agent import agent as crud_agent
from app.models.agent import Agent
from app.models.user_script import UserScript
from app.schemas.agent import AgentCreate, AgentUpdate, AgentClone

logger = logging.getLogger(__name__)

class AgentService:
    """
    Agent 领域服务
    职责：处理 Agent 相关的复杂业务逻辑，协调 CRUD 与跨模型操作。
    """

    async def get_agent_or_fail(self, db: AsyncSession, agent_id: str) -> Agent:
        """统一的获取检查，失败直接抛出异常，减少重复逻辑"""
        db_obj = await crud_agent.get(db, agent_id)
        if not db_obj:
            raise EntityNotFoundException(entity="Agent", identifier=agent_id)
        return db_obj

    async def create_agent(self, db: AsyncSession, obj_in: AgentCreate) -> Agent:
        """
        创建智能体及其初始生态系统（如默认脚本）
        """
        try:
            # 1. 持久化 Agent 基础信息 (不提交事务)
            db_obj = await crud_agent.create(db, obj_in=obj_in, commit=False)
            
            # 2. 编排业务逻辑：创建默认初始化脚本
            await self._create_default_script(db, db_obj.id)
            
            # 3. 统一提交
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create agent: {str(e)}")
            raise ServiceException(detail=_("Could not create agent ecosystem."))

    async def clone_agent(self, db: AsyncSession, agent_id: str, clone_in: AgentClone) -> Agent:
        """
        基于已有智能体进行深度克隆
        """
        original = await self.get_agent_or_fail(db, agent_id)

        # P10 技巧：利用字段排除和自动映射，避免 Hardcoding 导致的维护灾难
        # 排除不需要克隆的字段（PK、时间戳等）
        excluded_fields = {"id", "created_at", "updated_at"}
        original_data = {
            c.name: getattr(original, c.name) 
            for c in original.__table__.columns 
            if c.name not in excluded_fields
        }

        # 应用用户自定义覆盖
        original_data.update({
            "name": clone_in.name or f"{original.name} (Copy)",
            "is_template": clone_in.is_template,
            "is_active": True
        })

        agent_in = AgentCreate(**original_data)
        return await self.create_agent(db, agent_in)

    async def delete_agents(self, db: AsyncSession, agent_ids: List[str]) -> List[str]:
        """
        高性能批量删除
        """
        if not agent_ids:
            return []

        try:
            # P10 技巧：使用 SQLAlchemy 2.0 风格的批量删除，而非循环
            stmt = delete(Agent).where(Agent.id.in_(agent_ids))
            result = await db.execute(stmt)
            await db.commit()
            
            logger.info(f"Bulk deleted {result.rowcount} agents")
            return agent_ids
        except Exception as e:
            await db.rollback()
            logger.error(f"Bulk delete failed: {str(e)}")
            raise ServiceException(detail=_("Failed to perform batch deletion."))

    async def update_agent(self, db: AsyncSession, agent_id: str, obj_in: AgentUpdate) -> Agent:
        db_obj = await self.get_agent_or_fail(db, agent_id)
        return await crud_agent.update(db, db_obj=db_obj, obj_in=obj_in)

    async def get_agents(
        self, 
        db: AsyncSession, 
        *,
        skip: int = 0, 
        limit: int = 100, 
        **filters
    ) -> Sequence[Agent]:
        """支持动态过滤的分页查询"""
        return await crud_agent.get_multi(
            db, skip=skip, limit=limit, **filters
        )

    # --- Private Business Logic Helpers ---

    async def _create_default_script(self, db: AsyncSession, agent_id: str) -> None:
        """
        私有逻辑：封装 Agent 创建时的附随业务
        """
        default_script = UserScript(
            agent_id=agent_id,
            title=_("Default Script"),
            content=_("# Default Script\n\nThis is an auto-generated script template."),
            sort_order=0
        )
        db.add(default_script)

# 单例建议通过依赖注入（FastAPI Depends）管理，但在传统 Service 层可保留
agent_service = AgentService()