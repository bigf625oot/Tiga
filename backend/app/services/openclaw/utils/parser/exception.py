class TaskParsingError(Exception):
    """
    任务解析失败异常
    
    Attributes:
        raw_response (str): 原始 LLM 响应内容
        validation_error (str): 验证错误详情
        retry_count (int): 已重试次数
    """
    def __init__(self, raw_response: str, validation_error: str, retry_count: int = 0):
        self.raw_response = raw_response
        self.validation_error = validation_error
        self.retry_count = retry_count
        super().__init__(f"Task parsing failed after {retry_count} retries. Error: {validation_error}")
