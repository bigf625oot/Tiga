import json
import logging
from agno.tools import Toolkit
from app.services.knowledge.graph.analysis.nl2chart import KGQueryService
from app.services.indus_agent.chatbi.vanna.service import data_query_service
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class DataToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="data_toolkit")
        self.register(self.generate_kg_chart)
        self.register(self.query_database)

    async def generate_kg_chart(self, question: str) -> str:
        """
        根据自然语言问题生成知识图谱相关的图表配置。
        
        Args:
            question: 用户的自然语言问题
            
        Returns:
            JSON 字符串格式的图表配置
        """
        try:
            service = KGQueryService.get_instance()
            # generate_chart is async
            chart = await service.generate_chart(question)
            if chart:
                return json.dumps(chart, ensure_ascii=False)
            return "未能生成图表，图谱中可能没有相关数据。"
        except Exception as e:
            logger.error(f"KG Query failed: {e}")
            return f"图谱查询出错: {str(e)}"

    async def query_database(self, question: str) -> str:
        """
        将自然语言转换为 SQL 并查询数据库，返回查询结果和可能的图表配置。
        
        Args:
            question: 用户的自然语言问题
            
        Returns:
            JSON 字符串，包含 sql, data (markdown表格), chart (如有)
        """
        try:
            hints = await run_in_threadpool(data_query_service.semantic_layer.get_context_hints, question)
            q_with_context = f"{question}\n\n{hints}" if hints else question
            
            sql = await run_in_threadpool(data_query_service.vanna_core.generate_sql, q_with_context)
            if not sql or sql.startswith("--"): 
                return "抱歉，未能生成有效的 SQL 查询。"
            
            if not data_query_service.permission_validator.is_safe(sql): 
                return "SQL 安全校验未通过：包含禁止的关键字或操作。"
            
            df = await run_in_threadpool(data_query_service.vanna_core.run_sql, sql)
            if df.empty: 
                return "查询已执行，但未返回结果。"
            
            chart = None
            try:
                if len(df) == 1 and df.iloc[0].isnull().all():
                     pass
                else:
                     chart = await run_in_threadpool(data_query_service.vanna_core.generate_echarts, question, df, sql)
            except Exception as e:
                logger.warning(f"Chart generation failed: {e}")
            
            result = {
                "sql": sql,
                "data_summary": df.head(10).to_markdown(),
                "chart": chart
            }
            return json.dumps(result, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Database Query failed: {e}")
            return f"数据库查询出错: {str(e)}"
