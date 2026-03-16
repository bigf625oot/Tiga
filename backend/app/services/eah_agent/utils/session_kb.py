import os
import logging
from typing import Optional, List
from pathlib import Path

# Agno Imports
try:
    from agno.vectordb.lancedb import LanceDb
    from agno.knowledge import Knowledge as VectorKnowledgeBase
    from agno.knowledge.embedder.openai import OpenAIEmbedder
    from agno.knowledge.document import Document
    from agno.knowledge.reader.pdf_reader import PDFReader
    from agno.knowledge.reader.text_reader import TextReader
    HAS_AGNO_KB = True
except ImportError:
    HAS_AGNO_KB = False
    VectorKnowledgeBase = None
    LanceDb = None
    OpenAIEmbedder = None
    PDFReader = None
    TextReader = None

logger = logging.getLogger(__name__)

class SessionKnowledgeManager:
    """
    Manages a temporary, session-scoped Knowledge Base using LanceDB.
    """
    def __init__(self, session_id: str, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to backend/data/sessions
            backend_dir = Path(__file__).resolve().parents[4]
            base_dir = str(backend_dir / "data" / "sessions")
            
        self.session_id = session_id
        self.base_dir = Path(base_dir) / session_id
        self.kb_dir = self.base_dir / "knowledge"
        self.lancedb_uri = self.base_dir / "lancedb"
        
        # Ensure directories exist
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.lancedb_uri.mkdir(parents=True, exist_ok=True)
        
        self.kb: Optional[VectorKnowledgeBase] = None

    def get_knowledge_base(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> Optional[VectorKnowledgeBase]:
        """
        Returns the configured Knowledge Base instance.
        """
        if not HAS_AGNO_KB:
            logger.warning("Agno Knowledge Base dependencies not met.")
            return None

        if self.kb:
            return self.kb

        try:
            # Configure Embedder
            # Default to OpenAIEmbedder using the provided key or env
            embedder = OpenAIEmbedder(
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                base_url=base_url or os.getenv("OPENAI_BASE_URL"),
                id="text-embedding-3-small" # Efficient default
            )

            # Initialize LanceDB
            vector_db = LanceDb(
                table_name=f"session_{self.session_id}",
                uri=str(self.lancedb_uri),
                embedder=embedder,
            )

            # Initialize Knowledge Base
            self.kb = VectorKnowledgeBase(
                vector_db=vector_db,
                # Readers are used when loading files
                # We don't need to specify them here if we pass Documents directly, 
                # but good to have for load()
            )
            return self.kb
            
        except Exception as e:
            logger.error(f"Failed to initialize Session Knowledge Base: {e}")
            return None

    def add_file(self, file_path: str) -> bool:
        """
        Adds a file to the knowledge base.
        """
        if not self.kb:
            logger.warning("KB not initialized. Call get_knowledge_base first.")
            return False
            
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return False

            # Use Agno's load mechanism
            # It automatically selects reader based on extension if supported
            # or we can manually read and create Documents
            
            ext = file_path_obj.suffix.lower()
            reader = None
            
            if ext == ".pdf":
                reader = PDFReader()
            elif ext in [".txt", ".md", ".json", ".py", ".js"]:
                reader = TextReader()
            
            if reader:
                documents = reader.read(file_path_obj)
                if documents:
                    self.kb.load_documents(documents, upsert=True)
                    return True
            
            # Fallback for unsupported types: treat as text if readable
            try:
                content = file_path_obj.read_text(encoding="utf-8", errors="ignore")
                doc = Document(content=content, meta_data={"file_name": file_path_obj.name})
                self.kb.load_documents([doc], upsert=True)
                return True
            except Exception:
                pass

            return False
            
        except Exception as e:
            logger.error(f"Error adding file {file_path} to KB: {e}")
            return False

    def cleanup(self) -> bool:
        """
        Removes the session knowledge base and temporary files.
        """
        try:
            import shutil
            
            # Close connection if needed (Agno/LanceDB might handle this automatically, 
            # but explicit cleanup is safer)
            self.kb = None
            
            # Remove directories
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                logger.info(f"Cleaned up session KB for {self.session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup session KB {self.session_id}: {e}")
            return False
