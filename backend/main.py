from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv
import os
import requests
import json
from llm.groq_client import GroqClient
import chromadb
import pandas as pd
import logging
from typing import Dict, Any

app = FastAPI()
load_dotenv()

# Check for required environment variables
GROQCLOUD_API_URL = os.getenv("GROQCLOUD_API_URL")
GROQCLOUD_API_KEY = os.getenv("GROQCLOUD_API_KEY")

if not GROQCLOUD_API_URL or not GROQCLOUD_API_KEY:
    raise ValueError("GroqCloud API URL and API Key must be set in environment variables.")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="."), name="static")
# Serve index.html
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html") as f:
        return f.read()

# Helper function to read PDF
def read_pdf(file: BytesIO) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Helper function to read DOCX
def read_docx(file: BytesIO) -> str:
    document = Document(file)
    text = ""
    for para in document.paragraphs:
        text += para.text + "\n"
    return text

# Helper function to read TXT
def read_txt(file: BytesIO) -> str:
    return file.read().decode('utf-8')

# Function to use GroqCloud API for key clause extraction
def analyze_key_clauses_with_groqcloud(text: str) -> dict:
    try:
        # Truncate text to approximately 4000 tokens (roughly 16000 characters)
        MAX_CHARS = 16000
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "... (truncated)"
            logger.info(f"Text truncated to {MAX_CHARS} characters to meet token limits")

        messages = [
            {
                "role": "system",
                "content": """You are a contract analyzer. Extract the key clauses from the provided contract and return them in a JSON-like format, strictly adhering to this structure:
                {
                  "clauses": [
                    {
                      "clause": "<clause title>",
                      "description": "<brief description>"
                    }
                  ]
                }"""
            },
            {
                "role": "user",
                "content": text
            }
        ]

        data = {
            "messages": messages,
            "model": "llama3-8b-8192",
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_tokens": 2000  # Explicitly limit response tokens
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQCLOUD_API_KEY}"
        }

        response = requests.post(GROQCLOUD_API_URL, json=data, headers=headers)

        if response.status_code != 200:
            return {"error": f"GroqCloud API Error: {response.status_code} - {response.text}"}

        response_data = response.json()
        result_content = response_data["choices"][0]["message"]["content"]

        try:
            result_json = json.loads(result_content)
            return result_json
        except json.JSONDecodeError as json_err:
            return {"error": f"Invalid JSON received: {str(json_err)}", "content": result_content}

    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request error: {str(req_err)}"}
    except Exception as e:
        return {"error": f"Exception during processing: {str(e)}"}

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content with size check
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                content={"error": "File size exceeds maximum limit of 10MB"},
                status_code=400
            )

        file_type = file.content_type
        logger.info(f"Processing file: {file.filename} of type: {file_type}")

        # Extract text based on file type
        try:
            if file_type == "application/pdf":
                text = read_pdf(BytesIO(content))
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = read_docx(BytesIO(content))
            elif file_type == "text/plain":
                text = read_txt(BytesIO(content))
            else:
                return JSONResponse(
                    content={"error": f"Unsupported file type: {file_type}"},
                    status_code=400
                )

            if not text.strip():
                return JSONResponse(
                    content={"error": "No text could be extracted from the file"},
                    status_code=400
                )

            # Analyze key clauses
            analysis_result = analyze_key_clauses_with_groqcloud(text)

            # Check for errors in analysis_result
            if "error" in analysis_result:
                logger.error(f"Analysis error: {analysis_result['error']}")
                return JSONResponse(
                    content={"error": analysis_result["error"]},
                    status_code=500
                )

            # Return the analysis result as JSON
            return {
                "clauses": analysis_result.get("clauses", []),
                "file_name": file.filename,
                "file_type": file_type
            }

        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            return JSONResponse(
                content={"error": f"Error processing file: {str(e)}"},
                status_code=500
            )

    except Exception as e:
        logger.error(f"Unexpected error in upload_file: {str(e)}")
        return JSONResponse(
            content={"error": "An unexpected error occurred while processing the file"},
            status_code=500
        )
    finally:
        # Ensure file is closed
        await file.close()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/analyze/")
async def analyze_contract(request: dict):
    try:
        # Extract contract text from request but limit the size
        contract_text = "\n".join([f"{clause['clause']}: {clause['description']}" 
                                   for clause in request.get("clauses", [])])
        
        # Truncate text if it's too long (using 16k for main content)
        MAX_TEXT_LENGTH = 16000
        if len(contract_text) > MAX_TEXT_LENGTH:
            contract_text = contract_text[:MAX_TEXT_LENGTH] + "... (truncated)"
            logger.warning(f"Contract text truncated from {len(contract_text)} to {MAX_TEXT_LENGTH} characters")

        # Get similar contract with smaller length limit
        try:
            collection = chroma_client.get_collection(name="DatasetEx")
            similar_results = collection.query(
                query_texts=[contract_text],
                n_results=1
            )
            similar_contract = similar_results["documents"][0][0] if similar_results["documents"] else None
            
            # Truncate similar contract to smaller size
            SIMILAR_MAX_LENGTH = 8000  # Smaller limit for similar contract
            if similar_contract and len(similar_contract) > SIMILAR_MAX_LENGTH:
                similar_contract = similar_contract[:SIMILAR_MAX_LENGTH] + "... (truncated)"
            
            logger.info("Successfully retrieved similar contract from ChromaDB")
        except Exception as db_error:
            logger.error(f"ChromaDB error: {db_error}")
            similar_contract = None

        # Keep the original system prompt but with clearer formatting
        system_prompt = """You are a contract analysis AI. Your task is to analyze the given contract and provide a structured response in valid JSON format. 

                    **Objective:** Evaluate the contract for compliance, identify strengths and weaknesses, assess legal risks, and suggest actionable recommendations. Compare the contract with similar contracts and provide insights on alignment with industry standards.

                    **Instructions:**
                    - Calculate "Score" as a number between 0-100, based on the overall compliance, clarity, and completeness of the contract.
                    - Determine "Compliance_Level" (High, Medium, Low) based on compliance with standard legal and regulatory requirements.
                    - For "Strengths," list key elements that enhance the contract's effectiveness or compliance.
                    - For "Improvement_Areas," identify ambiguous, missing, or non-compliant clauses that require attention.
                    - For "Legal_Risks," highlight any clauses or areas that could lead to legal exposure or disputes.
                    - For "Recommendations," provide actionable steps to address improvement areas and mitigate risks.
                    - For "Similar_Contract_Analysis," compare this contract to industry-standard contracts or a dataset of similar agreements. Highlight differences, alignments, or notable deviations.

                    **Expected Output:** Return ONLY a JSON object structured as follows:
                    {
                        "Score": <number between 0-100>,
                        "Score_Reasoning": "<brief explanation for the score>",
                        "Compliance_Level": "<string: High|Medium|Low>",
                        "Compliance_Reasoning": "<brief explanation for the compliance level>",
                        "Strengths": ["<string>", ...],
                        "Improvement_Areas": ["<string>", ...],
                        "Legal_Risks": ["<string>", ...],
                        "Recommendations": ["<string>", ...],
                        "Similar_Contract_Analysis": "<string>"
                    }

                    **Example:**
                    {
                        "Score": 85,
                        "Score_Reasoning": "The contract is highly compliant with legal and regulatory requirements.",
                        "Compliance_Level": "High",
                        "Compliance_Reasoning": "The contract meets all legal and regulatory requirements.",
                        "Strengths": ["Well-defined termination clause", "Clear dispute resolution process"],
                        "Improvement_Areas": ["Ambiguity in confidentiality clause", "Missing data protection provisions"],
                        "Legal_Risks": ["Potential exposure to jurisdictional disputes", "Insufficient coverage for force majeure events"],
                        "Recommendations": ["Clarify confidentiality clause to avoid misinterpretation", "Include a comprehensive data protection clause aligned with GDPR"],
                        "Similar_Contract_Analysis": "The contract aligns with 90% of industry standards but lacks specific details on data protection compared to similar contracts."
                    }

                    Please ensure the output is concise, detailed, and aligned with the structure above."""


        # Make Groq API call with both contracts but optimized structure
        try:
            groq_client = GroqClient(GROQCLOUD_API_KEY)
            user_content = f"""Main Contract:
{contract_text}

Similar Contract:
{similar_contract if similar_contract else 'No similar contract found'}"""

            response = groq_client.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            
            # Get the response content
            response_content = response.choices[0].message.content
            
            try:
                # Try to parse the JSON response
                analysis_result = json.loads(response_content)
                return JSONResponse(content=analysis_result, status_code=200)
            except json.JSONDecodeError as json_err:
                # Return a fallback response without logging the raw response
                return JSONResponse(
                    content={
                        "Score": 0,
                        "Score_Reasoning": "Analysis failed - JSON parsing error",
                        "Compliance_Level": "Error",
                        "Compliance_Reasoning": "Analysis failed - JSON parsing error",
                        "Strengths": [],
                        "Improvement_Areas": ["Could not parse analysis results"],
                        "Legal_Risks": ["Analysis failed - JSON parsing error"],
                        "Recommendations": ["Please try again"],
                        "Similar_Contract_Analysis": "Analysis failed"
                    },
                    status_code=200
                )
            
        except Exception as api_err:
            logger.error("Error calling Groq API")
            return JSONResponse(
                content={
                    "Score": 0,
                    "Score_Reasoning": "API error occurred",
                    "Compliance_Level": "Error",
                    "Compliance_Reasoning": "API error occurred",
                    "Strengths": [],
                    "Improvement_Areas": ["API error occurred"],
                    "Legal_Risks": ["Analysis incomplete"],
                    "Recommendations": ["Please try again"],
                    "Similar_Contract_Analysis": "Analysis failed"
                },
                status_code=200
            )
    
    except Exception as e:
        logger.error("General error in analyze_contract")
        return JSONResponse(
            content={
                "Score": 0,
                "Score_Reasoning": "System error occurred",
                "Compliance_Level": "Error",
                "Compliance_Reasoning": "System error occurred",
                "Strengths": [],
                "Improvement_Areas": ["System error occurred"],
                "Legal_Risks": ["Analysis incomplete"],
                "Recommendations": ["Please try again"],
                "Similar_Contract_Analysis": "Analysis failed"
            },
            status_code=200
        )

# Initialize ChromaDB and create collection
def initialize_chromadb():
    try:
        # Initialize ChromaDB client
        chroma_client = chromadb.Client()
        collection_name = "DatasetEx"

        # Check if collection exists, if not create it
        try:
            collection = chroma_client.get_collection(name=collection_name)
            print(f"Collection {collection_name} already exists")
        except Exception:
            print(f"Creating new collection: {collection_name}")
            collection = chroma_client.create_collection(name=collection_name)
            
            # Load your CSV data
            file = "dataset.csv"
            try:
                df = pd.read_csv(file)
                
                # Add an ID column if it doesn't exist
                df["ID"] = ["doc_" + str(i) for i in range(len(df))]

                # Prepare documents using f-strings
                documents = df.apply(
                    lambda row: (
                        f"Document Name: {row['Document Name']} | "
                        f"Effective Date: {row['Effective Date']} | "
                        f"Category: {row['Category']} | "
                        f"Parties Involved: {row['Parties']} | "
                        f"Agreement Date: {row['Agreement Date']} | "
                        f"Expiration Date: {row['Expiration Date']} | "
                        f"Renewal Term: {row['Renewal Term']} | "
                        f"Governing Law: {row['Governing Law']} | "
                        f"Exclusivity: {row['Exclusivity']} | "
                        f"Contract Details: {row['contract']}"
                    ),
                    axis=1
                ).tolist()

                # Extract metadata
                metadata = df[["Document Name", "Effective Date", "Category"]].to_dict(orient="records")
                ids = df["ID"].tolist()

                # Add data to the ChromaDB collection
                collection.add(documents=documents, metadatas=metadata, ids=ids)
                print(f"Added {len(documents)} records to the ChromaDB collection")
            except Exception as e:
                print(f"Error loading CSV data: {str(e)}")
                # Create a dummy document if CSV loading fails
                collection.add(
                    documents=["Sample contract document"],
                    metadatas=[{"source": "dummy"}],
                    ids=["dummy_1"]
                )
                
        return chroma_client
    except Exception as e:
        print(f"Error initializing ChromaDB: {str(e)}")
        return None

# Initialize ChromaDB at startup
chroma_client = initialize_chromadb()

