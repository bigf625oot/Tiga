import json
import time
import logging
import asyncio
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from app.core.config import settings

logger = logging.getLogger(__name__)

class AliyunASRService:
    def __init__(self):
        self.access_key = settings.ALIYUN_ACCESS_KEY_ID
        self.access_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        self.app_key = settings.ALIYUN_APP_KEY
        self.region_id = "cn-shanghai" # Default region for NLS
        self.domain = "filetrans.cn-shanghai.aliyuncs.com"
        self.version = "2018-08-17"
        
        if self.access_key and self.access_secret:
            self.client = AcsClient(self.access_key, self.access_secret, self.region_id)
        else:
            self.client = None
            logger.warning("Aliyun AccessKey not configured. ASR will run in mock mode.")

    def _create_request(self, action, params=None, method='POST'):
        request = CommonRequest()
        request.set_domain(self.domain)
        request.set_version(self.version)
        request.set_product('nls-filetrans')
        request.set_action_name(action)
        request.set_method(method)
        if params:
            for k, v in params.items():
                request.add_body_params(k, v)
        return request

    def submit_task(self, file_url):
        if not self.client:
            return "mock_task_id"
            
        task = {
            "appkey": self.app_key,
            "file_link": file_url,
            "version": "4.0",
            "enable_words_valid": True,
            "enable_callback": False
        }
        
        request = self._create_request('SubmitTask')
        request.add_body_params('Task', json.dumps(task))
        
        try:
            response = self.client.do_action_with_exception(request)
            response_json = json.loads(response)
            if response_json['StatusText'] == 'SUCCESS':
                return response_json['TaskId']
            else:
                logger.error(f"Failed to submit task: {response_json}")
                return None
        except Exception as e:
            logger.error(f"Aliyun SubmitTask Error: {e}")
            return None

    def get_task_result(self, task_id):
        if not self.client or task_id == "mock_task_id":
            return {"status": "SUCCESS", "text": "【Mock】这是本地模拟的转写结果。请配置阿里云 AccessKey 以启用真实转写。", "sentences": []}

        request = self._create_request('GetTaskResult', method='GET')
        request.add_query_param('TaskId', task_id)
        
        try:
            response = self.client.do_action_with_exception(request)
            response_json = json.loads(response)
            status_text = response_json['StatusText']
            
            if status_text == 'SUCCESS':
                result = response_json.get('Result', {})
                sentences = result.get('Sentences', [])
                full_text = "".join([s.get('Text', '') for s in sentences])
                return {"status": "SUCCESS", "text": full_text, "sentences": sentences}
            elif status_text == 'SUCCESS_WITH_NO_VALID_FRAGMENT':
                return {"status": "SUCCESS", "text": "【提示】未检测到有效语音片段（可能是静音或噪音）", "sentences": []}
            elif status_text in ['RUNNING', 'QUEUEING']:
                return {"status": "RUNNING"}
            else:
                logger.error(f"Task Failed: {response_json}")
                return {"status": "FAILED", "error": status_text}
                
        except Exception as e:
            logger.error(f"Aliyun GetTaskResult Error: {e}")
            return {"status": "FAILED", "error": str(e)}

    async def transcribe_audio(self, file_url):
        """
        Async wrapper to submit and poll for result
        """
        task_id = self.submit_task(file_url)
        if not task_id:
            return None
            
        # Polling
        max_retries = 60 # 2 minutes max for demo
        for _ in range(max_retries):
            result = self.get_task_result(task_id)
            status = result.get("status")
            
            if status == "SUCCESS":
                return result.get("text")
            elif status == "FAILED":
                return f"Transcription Failed: {result.get('error')}"
            
            await asyncio.sleep(2)
            
        return "Transcription Timeout"

aliyun_asr_service = AliyunASRService()
