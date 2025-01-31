from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .services.contract_service import ContractService
from .services.llm_service import LLMService
from .utils.config import Config
from .data.database import ChromaDBManager

def create_app():
    app = FastAPI()
    config = Config()
    
    # Initialize services
    llm_service = LLMService(config.groqcloud_api_key)
    contract_service = ContractService(llm_service)
    db_manager = ChromaDBManager()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="."), name="static")
    
    # Register routes
    @app.post("/uploadfile/")
    async def upload_file(file: UploadFile = File(...)):
        return await contract_service.process_contract(file)
    
    @app.post("/analyze/")
    async def analyze_contract(request: dict):
        return contract_service.analyze_contract(request)
    
    return app

app = create_app() 