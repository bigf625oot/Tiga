import json
import logging
import uuid
import re
from typing import List, Optional, Dict, Any, Union
from functools import lru_cache
import pandas as pd
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import EmbeddingFunctionRegistry
from openai import OpenAI
import sqlparse

from app.core.config import settings
from .runners.sql_runner import SQLAlchemyRunner

logger = logging.getLogger(__name__)

# --- Data Models for LanceDB ---
# Make vector dimension dynamic
# The 'vector' field is handled as a plain list in Pydantic, 
# but LanceDB will infer the correct FixedSizeList from the first inserted data.
class VannaContext(LanceModel):
    id: str
    text: str = ""
    type: str # "ddl", "sql", "doc"
    # Using dynamic vector dimension instead of hardcoded Vector(1536)
    vector: List[float] = Vector(1536) 

# --- Core Vanna Engine (Re-implementation for Vanna 2.0 / Custom RAG) ---
class VannaCore:
    def __init__(self, db_path: str = "data/vanna_lancedb"):
        self.db = lancedb.connect(db_path)
        # We don't pre-create the table here because we don't know the embedding dimension yet.
        # It will be created/opened on first write or read.
        self.table_name = "vanna_context"
        self.table = None
        
        self.openai_client: Optional[OpenAI] = None
        self.embed_client: Optional[OpenAI] = None
        self.model = "gpt-3.5-turbo" # Default, will be overwritten by config
        self.embed_model = "text-embedding-3-small"
        self.sql_runner: Optional[SQLAlchemyRunner] = None
        self._sql_cache = {} # Simple in-memory cache for SQL generation

    def configure_llm(self, api_key: str, base_url: str = None, model: str = None, 
                      embedding_api_key: str = None, embedding_base_url: str = None, embedding_model: str = None):
        """Configure the LLM client dynamically."""
        if not api_key:
            raise ValueError("API Key is required for VannaCore")
        
        self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
        if model:
            self.model = model
            
        # Configure Embedding Client (if different from Chat)
        if embedding_api_key:
            self.embed_client = OpenAI(api_key=embedding_api_key, base_url=embedding_base_url)
            self.embed_model = embedding_model
        else:
            # Fallback to same client if no specific embedding config
            self.embed_client = self.openai_client
            # Try to respect the chat model if it looks like an embedding one (unlikely but possible)
            # or default to standard openai
            self.embed_model = "text-embedding-3-small"
            
        logger.info(f"VannaCore configured. Chat Model: {self.model}, Embed Model: {self.embed_model}")

    def set_sql_runner(self, runner: SQLAlchemyRunner):
        self.sql_runner = runner

    def _check_llm_configured(self):
        if not self.openai_client:
            raise RuntimeError("LLM not configured. Please configure OpenAI/LLM settings first.")

    def _get_embedding(self, text: str) -> List[float]:
        self._check_llm_configured()
        text = text.replace("\n", " ")
        
        try:
            return self.embed_client.embeddings.create(input=[text], model=self.embed_model).data[0].embedding
        except Exception as e:
            # Fallback strategy only if using default model and it fails
            if self.embed_model == "text-embedding-3-small":
                logger.warning(f"Embedding failed with {self.embed_model}, trying text-embedding-ada-002. Error: {e}")
                return self.embed_client.embeddings.create(input=[text], model="text-embedding-ada-002").data[0].embedding
            raise e

    def _ensure_table(self, dimension: int = 1536):
        """Ensure the table exists and check dimension compatibility."""
        if self.table:
            # Table already opened in memory
            return

        # Try to open existing table
        try:
            self.table = self.db.open_table(self.table_name)
        except Exception:
            # Table doesn't exist, we will create it on first write
            pass

    def reset_vector_store(self):
        """Clear all vector data."""
        try:
            self.db.drop_table(self.table_name)
            self.table = None
            logger.info(f"Vector store '{self.table_name}' cleared successfully.")
        except Exception as e:
            logger.warning(f"Failed to clear vector store (maybe it didn't exist): {e}")

    def train(self, ddl: str = None, sql: str = None, documentation: str = None) -> List[str]:
        """Add context to the vector store."""
        self._check_llm_configured()
        
        # Collect data points
        data = []
        
        if ddl:
            vec = self._get_embedding(ddl)
            data.append({"id": str(uuid.uuid4()), "text": ddl, "type": "ddl", "vector": vec})
        if sql:
            vec = self._get_embedding(sql)
            data.append({"id": str(uuid.uuid4()), "text": sql, "type": "sql", "vector": vec})
        if documentation:
            vec = self._get_embedding(documentation)
            data.append({"id": str(uuid.uuid4()), "text": documentation, "type": "doc", "vector": vec})
            
        if not data:
            return []

        # Get dimension from the first vector
        dim = len(data[0]["vector"])
        
        try:
            # 1. Try to open existing table
            if not self.table:
                try:
                    self.table = self.db.open_table(self.table_name)
                except:
                    # Table not found
                    pass

            # 2. If table exists, try to add
            if self.table:
                try:
                    self.table.add(data)
                except Exception as e:
                    # If dimension mismatch error (ArrowInvalid), drop and recreate
                    if "FixedSizeListType" in str(e) or "dimension" in str(e).lower():
                        logger.warning(f"Vector dimension mismatch (expected different dim, got {dim}). Recreating table...")
                        self.db.drop_table(self.table_name)
                        self.table = self.db.create_table(self.table_name, data=data)
                    else:
                        raise e
            else:
                # 3. Create new table
                self.table = self.db.create_table(self.table_name, data=data)
                
            return [d["id"] for d in data]
            
        except Exception as e:
            logger.error(f"Failed to train/add to vector store: {e}")
            raise e

    def get_related_context(self, question: str, limit: int = 10) -> List[str]:
        """Retrieve related DDL/SQL/Docs."""
        self._check_llm_configured()
        
        # Open table if not opened
        if not self.table:
            try:
                self.table = self.db.open_table(self.table_name)
            except:
                # Table doesn't exist yet (no training data)
                return []
                
        try:
            query_vec = self._get_embedding(question)
            results = self.table.search(query_vec).limit(limit).to_list()
            return [r["text"] for r in results]
        except Exception as e:
            err_msg = str(e).lower()
            # Handle dimension mismatch (e.g. switching from OpenAI 1536 to other 1024 models)
            if "dimension mismatch" in err_msg or "query dim" in err_msg or "invalid user input" in err_msg:
                logger.warning(f"Vector dimension mismatch detected: {e}. Dropping incompatible table '{self.table_name}' to force rebuild on next train.")
                try:
                    self.db.drop_table(self.table_name)
                    self.table = None
                except Exception as drop_err:
                    logger.error(f"Failed to drop incompatible table: {drop_err}")
            else:
                logger.warning(f"Search failed: {e}")
            return []

    def classify_intent(self, question: str) -> str:
        """Classify user intent: aggregation, time_series, comparison, detail, or unknown."""
        self._check_llm_configured()
        system_prompt = """You are a Query Intent Classifier.
Classify the user's question into one of the following categories:
- aggregation: Questions asking for counts, sums, averages, stats.
- time_series: Questions asking for trends over time, daily/monthly data.
- comparison: Questions comparing two or more entities or periods.
- detail: Questions asking for specific records or lists.
- unknown: If the intent is unclear.

Return ONLY the category name.
"""
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip().lower()

    def generate_sql(self, question: str) -> str:
        """RAG-based SQL Generation with Caching."""
        self._check_llm_configured()
        # Check Cache
        if question in self._sql_cache:
            logger.info(f"Cache hit for question: {question}")
            return self._sql_cache[question]

        context = self.get_related_context(question)
        
        system_prompt = """You are an expert SQL Data Analyst.
Your task is to generate a SQL query to answer the user's question.
You MUST use the provided context (DDL, SQL examples) to construct the query.
Return ONLY the SQL query, without markdown backticks or explanations.
If you cannot generate a query, return "-- I do not know".
"""
        
        user_prompt = f"""Question: {question}

Context:
{chr(10).join(context)}

Generate SQL:
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        
        sql = response.choices[0].message.content.strip()
        # Clean up markdown
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Cache Result
        if not sql.startswith("--"):
            self._sql_cache[question] = sql
            
        return sql

    def _mask_sensitive_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mask sensitive data like emails, phones, ID cards."""
        # Simple regex-based masking for demonstration
        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        # Phone (Simple 11 digit)
        phone_pattern = r'\b1[3-9]\d{9}\b'
        
        # Helper to mask string
        def mask_val(val):
            if not isinstance(val, str):
                return val
            if re.match(email_pattern, val):
                return re.sub(r'(^.{2}).*(@.*$)', r'\1***\2', val)
            if re.match(phone_pattern, val):
                return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', val)
            return val

        # Apply to object columns
        for col in df.select_dtypes(include=['object']):
             df[col] = df[col].apply(mask_val)
             
        return df

    def run_sql(self, sql: str) -> pd.DataFrame:
        """Execute SQL with Security Check and Masking."""
        if not self.sql_runner:
            raise Exception("Database not connected")
        
        # Security Check
        if not self._is_read_only(sql):
             raise Exception("Security Alert: Only SELECT queries are allowed.")

        df = self.sql_runner.run_sql(sql)
        
        # Data Masking
        df = self._mask_sensitive_data(df)
        
        return df

    def _is_read_only(self, sql: str) -> bool:
        """Simple SQL injection/mutation protection."""
        try:
            parsed = sqlparse.parse(sql)[0]
            return parsed.get_type().upper() == 'SELECT'
        except:
            # If parsing fails, assume unsafe
            return False

    def generate_echarts(self, question: str, df: pd.DataFrame, sql: str) -> Dict:
        """Generate ECharts option JSON."""
        self._check_llm_configured()
        if df.empty:
            return {}
            
        data_preview = df.head(5).to_markdown()
        columns = df.columns.tolist()
        
        system_prompt = """You are a Data Visualization Expert.
Your task is to generate an Apache ECharts option JSON object to visualize the provided data.
The JSON must be valid and ready to use in `echarts.setOption()`.
Return ONLY the JSON string.
"""
        
        user_prompt = f"""Question: {question}
SQL: {sql}
Data Preview:
{data_preview}
Columns: {columns}

Generate ECharts JSON:
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        
        json_str = response.choices[0].message.content.strip()
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(json_str)
        except:
            return {}

    def ask(self, question: str) -> Dict[str, Any]:
        """Main entry point."""
        sql = self.generate_sql(question)
        if sql.startswith("--"):
            return {"sql": sql, "error": "Could not generate SQL"}
            
        try:
            df = self.run_sql(sql)
            chart = self.generate_echarts(question, df, sql)
            
            return {
                "question": question,
                "sql": sql,
                "data": df.to_dict(orient="records"),
                "columns": df.columns.tolist(),
                "chart": chart
            }
        except Exception as e:
            return {"sql": sql, "error": str(e)}
