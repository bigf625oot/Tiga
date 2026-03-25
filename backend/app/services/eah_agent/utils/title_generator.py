"""
自动标题生成服务
场景：
    1. 会话开始时，根据用户输入自动生成会话标题
    2. 会话进行中，根据用户输入和系统状态智能更新标题
"""
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.storage.session_history import SessionHistory
from app.services.llm.resolver import resolve_fast_llm_model
from app.services.llm.factory import ModelFactory

logger = logging.getLogger(__name__)

class TitleGenerator:
    """
    自动标题生成服务：根据对话内容智能生成简短标题。
    优化点：异步非阻塞、语言自适应、鲁棒的正则清洗。
    """
    
    # 默认标题列表，匹配这些标题时才会触发自动更新
    DEFAULT_TITLES = {"New Chat", "新对话", "新任务", "Untitled", "未命名会话"}

    @classmethod
    async def generate_title(cls, session_id: str, db: AsyncSession):
        """
        为会话生成标题。建议作为 BackgroundTask 异步调用。
        """
        try:
            history = SessionHistory(db)
            session = await history.get_session(session_id)
            if not session:
                return

            # 1. 获取前 5 条消息作为上下文
            messages = await history.get_messages(session_id, limit=5)
            if not messages or len(messages) < 2:
                # 至少需要一问一答才能生成有意义的标题
                return

            # 2. 判断是否需要更新标题
            current_title = (session.title or "").strip()
            first_msg_content = messages[0].content or ""
            
            # 判定准则：标题是默认值 OR 标题只是第一句话的前 N 个字符（说明是系统临时截取的）
            is_default = current_title in cls.DEFAULT_TITLES or not current_title
            is_auto_truncated = (
                current_title == first_msg_content[:len(current_title)] 
                and len(current_title) <= 50
            )

            if not (is_default or is_auto_truncated):
                # 如果用户可能已经自定义了标题，则跳过，尊重用户选择
                return

            # 3. 准备模型
            llm_model = await resolve_fast_llm_model(db)
            if not llm_model:
                return
            model = ModelFactory.create_model(llm_model)

            # 4. 构建对话摘要上下文
            context_segments = []
            for msg in messages[:4]:
                role = "User" if msg.role == "user" else "Assistant"
                # 限制单条消息长度，防止浪费 Token
                text = (msg.content or "")[:400].replace("\n", " ")
                context_segments.append(f"{role}: {text}")
            
            conversation_summary = "\n".join(context_segments)

            # 5. 构造 Prompt (强制简洁，自适应语言)
            prompt = f"""
            Task: Create a concise, high-level title for this conversation.
            Requirements:
            - Maximum 10-15 characters.
            - Use the same language as the conversation (e.g., Chinese if the user speaks Chinese).
            - Output ONLY the title text. No quotes, no "Title:", no period.

            Conversation:
            {conversation_summary}
            """

            from agno.models.message import Message as AgnoMessage
            
            # 6. 异步调用 LLM
            try:
                # 生产环境建议使用异步方法避免阻塞
                response = await model.aresponse(messages=[AgnoMessage(role="user", content=prompt)])
                raw_title = response.content.strip() if response.content else ""
            except AttributeError:
                # 兼容同步方法
                response = model.response(messages=[AgnoMessage(role="user", content=prompt)])
                raw_title = response.content.strip() if response.content else ""

            # 7. 清洗标题数据
            new_title = cls._clean_title(raw_title)

            # 8. 更新数据库
            if new_title and new_title != current_title:
                # 再次校验避免模型生成了无意义的内容
                if len(new_title) > 1:
                    logger.info(f"Session {session_id}: Updating title to '{new_title}'")
                    await history.update_session_title(session_id, new_title)
                    await db.commit() # 确保后台任务提交事务

        except Exception as e:
            logger.error(f"Failed to generate title for session {session_id}: {str(e)}", exc_info=True)

    @staticmethod
    def _clean_title(title: str) -> str:
        """
        清洗模型生成的标题，去除冗余字符。
        """
        # 去除首尾引号、破折号、句号
        title = title.strip(" \"'《》-—。")
        
        # 移除模型常见的引导词，如 "Title:", "标题:", "Topic:" (不分大小写)
        title = re.sub(r'^(title|标题|topic|主题)\s*[:：]\s*', '', title, flags=re.IGNORECASE)
        
        # 再次清洗引号
        title = title.replace('"', '').replace("'", "")
        
        # 限制长度
        return title[:20]