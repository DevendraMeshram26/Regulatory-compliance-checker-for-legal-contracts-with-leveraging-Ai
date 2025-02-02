from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from app.services.file_readers import read_pdf, read_docx, read_txt
from app.services.groq_service import analyze_key_clauses_with_groqcloud
from io import BytesIO
from app.utils.logger import logger
from app.services.slack_service import SlackService
from config import Config

router = APIRouter()

# Initialize SlackService
slack_service = SlackService(Config.SLACK_WEBHOOK_URL)

@router.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename} with content type: {file.content_type}")
    try:
        content = await file.read()
        logger.info(f"File content read successfully, size: {len(content)} bytes")
        file_type = file.content_type

        if file_type == "application/pdf":
            text = read_pdf(BytesIO(content))
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = read_docx(BytesIO(content))
        elif file_type == "text/plain":
            text = read_txt(BytesIO(content))
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return JSONResponse(content={"error": "Unsupported file type"}, status_code=400)

        analysis_result = analyze_key_clauses_with_groqcloud(text)

        if "error" in analysis_result:
            logger.error(f"Analysis error: {analysis_result['error']}")
            slack_service.send_alert(f"Error processing file {file.filename}: {analysis_result['error']}")
            return JSONResponse(content={"error": analysis_result["error"]}, status_code=500)

        logger.info("File processed successfully, returning analysis result.")
        slack_service.send_alert(f"File processed successfully: {file.filename}")
        return {"clauses": analysis_result.get("clauses", []), "file_name": file.filename, "file_type": file_type}

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        slack_service.send_alert(f"Error processing file {file.filename}: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)