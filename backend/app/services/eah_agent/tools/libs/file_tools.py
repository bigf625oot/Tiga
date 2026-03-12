from typing import Optional, List
from agno.tools import Toolkit
from agno.tools.file import FileTools as AgnoFileTools
from pydantic import BaseModel, Field
import json
import os

class FileTools(AgnoFileTools):
    _name = "file_tools"
    _label = "文件管理 (File)"
    _description = "读取、写入、列出本地文件"
    """
    使用 FileTools 管理本地文件系统。
    """
    def __init__(self, base_dir: Optional[str] = None):
        super().__init__(base_dir=base_dir)

    class Config(BaseModel):
        base_dir: Optional[str] = Field(None, description="Base directory for file operations")

class PDFTools(Toolkit):
    _name = "pdf_tools"
    _label = "PDF 解析 (PDF)"
    _description = "解析 PDF 文档内容"
    """
    使用 PDFTools 从 PDF 文件中提取文本。
    """
    def __init__(self):
        super().__init__(name="pdf_tools")
        self.register(self.read_pdf)

    def read_pdf(self, file_path: str, pages: Optional[List[int]] = None) -> str:
        """
        Read text from a PDF file.
        :param file_path: Path to the PDF file
        :param pages: List of page numbers to read (0-indexed). If None, reads all pages.
        :return: Extracted text
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            
            if pages is None:
                pages = range(len(reader.pages))
                
            for i in pages:
                if i < len(reader.pages):
                    page = reader.pages[i]
                    text += f"--- Page {i+1} ---\n"
                    text += page.extract_text() + "\n\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    class Config(BaseModel):
        pass

class JSONTools(Toolkit):
    _name = "json_tools"
    _label = "JSON 工具 (JSON)"
    _description = "解析和验证 JSON 数据"
    """
    使用 JSONTools 处理 JSON 数据。
    """
    def __init__(self):
        super().__init__(name="json_tools")
        self.register(self.validate_json)
        self.register(self.pretty_print_json)
        self.register(self.query_json)

    def validate_json(self, json_str: str) -> str:
        """Check if a string is valid JSON."""
        try:
            json.loads(json_str)
            return "Valid JSON"
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"

    def pretty_print_json(self, json_str: str) -> str:
        """Format JSON string with indentation."""
        try:
            data = json.loads(json_str)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error formatting JSON: {str(e)}"

    def query_json(self, json_str: str, key: str) -> str:
        """Get a value from a JSON string by key (top-level only for now)."""
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return str(data.get(key, "Key not found"))
            return "JSON is not a dictionary"
        except Exception as e:
            return f"Error querying JSON: {str(e)}"

    class Config(BaseModel):
        pass
