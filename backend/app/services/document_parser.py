import io
from fastapi import UploadFile, HTTPException
import pypdf
import docx
import os
import logging

logger = logging.getLogger(__name__)

def parse_local_file(file_path: str) -> str:
    """
    Parse a local file and return text content.
    """
    filename = os.path.basename(file_path).lower()
    logger.info(f"Parsing local file: {file_path}")
    text = ""
    
    try:
        if filename.endswith('.pdf'):
            logger.info("Parsing PDF file...")
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text += page.extract_text() + "\n"
            logger.info(f"PDF parsed successfully. Pages: {len(reader.pages)}")
        elif filename.endswith('.docx'):
            logger.info("Parsing DOCX file...")
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            logger.info(f"DOCX parsed successfully. Paragraphs: {len(doc.paragraphs)}")
        else:
            # Try plain text
            logger.info("Parsing plain text file...")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except:
                try:
                    with open(file_path, "r", encoding="gbk") as f:
                        text = f.read()
                except:
                    pass
            logger.info("Plain text parsed.")
                    
        return sanitize_text(text.strip())
    except Exception as e:
        logger.error(f"Error parsing local file {file_path}: {e}")
        print(f"Error parsing local file {file_path}: {e}")
        return ""

def sanitize_text(text: str) -> str:
    """
    清洗文本，移除可能导致编码问题的非法字符（如单独的代理对）。
    """
    if not text:
        return ""
    # 1. 移除非法代理对 (surrogates)
    # 使用 errors='ignore' 忽略无法编码的字符，然后再解码回来
    cleaned = text.encode('utf-8', 'ignore').decode('utf-8')
    
    # 2. 移除空字符 (NUL) - 某些数据库如 Postgres 不支持
    cleaned = cleaned.replace('\x00', '')
    
    return cleaned

async def parse_document(file: UploadFile) -> str:
    """
    Parse uploaded document (PDF or Word) and return text content.
    """
    content_type = file.content_type
    filename = file.filename.lower()
    
    try:
        content = await file.read()
        file_stream = io.BytesIO(content)
        
        text = ""
        
        if filename.endswith('.pdf') or content_type == 'application/pdf':
            reader = pypdf.PdfReader(file_stream)
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="未提取到文本内容。如果是扫描版 PDF，请先使用 OCR 工具转换为可编辑文本。")
                
        elif filename.endswith(('.docx', '.doc')) or 'word' in content_type:
            # python-docx only supports .docx
            if filename.endswith('.doc'):
                raise HTTPException(status_code=400, detail="暂不支持旧版 .doc 格式，请另存为 .docx 后上传")
                
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
            if not text.strip():
                raise HTTPException(status_code=400, detail="未提取到文本内容。文档可能只包含图片或表格。")
        else:
            # Try to read as plain text
            try:
                text = content.decode('utf-8')
            except:
                # Try gbk
                try:
                    text = content.decode('gbk')
                except:
                    raise HTTPException(status_code=400, detail="无法解码文件内容，请确保是 UTF-8 或 GBK 编码的文本文件。")
                
        return sanitize_text(text.strip())
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error parsing document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")
