from fastapi import UploadFile
from ..utils.file_handlers import FileHandler
from ..services.llm_service import LLMService

class ContractService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.file_handler = FileHandler()

    async def process_contract(self, file: UploadFile):
        content = await file.read()
        text = self.file_handler.extract_text(content, file.content_type)
        return self.llm_service.analyze_key_clauses(text)

    def analyze_contract(self, clauses):
        # Contract analysis logic
        pass 