import io
from fastapi import UploadFile, HTTPException
import PyPDF2
import docx
import os

def parse_local_file(file_path: str) -> str:
    """
    Parse a local file and return text content.
    """
    filename = os.path.basename(file_path).lower()
    text = ""
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        file_stream = io.BytesIO(content)
        
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file_stream)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif filename.endswith('.docx'):
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            # Try plain text
            try:
                text = content.decode('utf-8')
            except:
                try:
                    text = content.decode('gbk')
                except:
                    # If not text, return empty or error
                    pass
                    
        return text.strip()
    except Exception as e:
        print(f"Error parsing local file {file_path}: {e}")
        return ""

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
            reader = PyPDF2.PdfReader(file_stream)
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
                
        return text.strip()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error parsing document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")
