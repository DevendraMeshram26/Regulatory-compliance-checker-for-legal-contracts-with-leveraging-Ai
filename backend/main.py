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
        # Define the messages and request body
        messages = [
            {
                "role": "system",
                "content": """You are a contract analyzer. Extract the key clauses from the provided contract and return them in a JSON-like format, strictly adhering to this structure:

                {
                  "clauses": [
                    {
                      "clause": "<clause title>",
                      "description": "<clause description>"
                    }
                  ]
                }

                Ensure the output is valid JSON. Avoid unnecessary information or deviations from this structure."""
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
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQCLOUD_API_KEY}"
        }

        # Make the API request
        response = requests.post(GROQCLOUD_API_URL, data=json.dumps(data), headers=headers)

        if response.status_code != 200:
            return {"error": f"GroqCloud API Error: {response.status_code} - {response.text}"}

        # Parse the response
        response_data = response.json()
        result_content = response_data["choices"][0]["message"]["content"]

        # Try to load JSON
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
        # Read file content
        content = await file.read()
        file_type = file.content_type

        # Extract text based on file type
        if file_type == "application/pdf":
            text = read_pdf(BytesIO(content))
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = read_docx(BytesIO(content))
        elif file_type == "text/plain":
            text = read_txt(BytesIO(content))
        else:
            return JSONResponse(content={"error": "Unsupported file type"}, status_code=400)

        # Analyze key clauses
        analysis_result = analyze_key_clauses_with_groqcloud(text)

        # Check for errors in analysis_result
        if "error" in analysis_result:
            return JSONResponse(content={"error": analysis_result["error"]}, status_code=500)

        # Return the analysis result as JSON
        return {"clauses": analysis_result.get("clauses", []), "file_name": file.filename, "file_type": file_type}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/analyze/")
async def analyze_contract(request: dict):
    try:
        # Extract contract text from request
        contract_text = "\n".join([f"{clause['clause']}: {clause['description']}" 
                                   for clause in request.get("clauses", [])])
        
        # Retrieve similar contract from ChromaDB
        try:
            collection = chroma_client.get_collection(name="DatasetEx")
            similar_results = collection.query(
                query_texts=[contract_text],
                n_results=1
            )
            similar_contract = similar_results["documents"][0][0] if similar_results["documents"] else None
            logger.info("Successfully retrieved similar contract from ChromaDB")
        except Exception as db_error:
            logger.error(f"ChromaDB error: {db_error}")
            similar_contract = None
        
        # Updated comprehensive system prompt for analysis
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
                        "Compliance_Level": "<string: High|Medium|Low>",
                        "Strengths": ["<string>", ...],
                        "Improvement_Areas": ["<string>", ...],
                        "Legal_Risks": ["<string>", ...],
                        "Recommendations": ["<string>", ...],
                        "Similar_Contract_Analysis": "<string>"
                    }

                    **Example:**
                    {
                        "Score": 85,
                        "Compliance_Level": "High",
                        "Strengths": ["Well-defined termination clause", "Clear dispute resolution process"],
                        "Improvement_Areas": ["Ambiguity in confidentiality clause", "Missing data protection provisions"],
                        "Legal_Risks": ["Potential exposure to jurisdictional disputes", "Insufficient coverage for force majeure events"],
                        "Recommendations": ["Clarify confidentiality clause to avoid misinterpretation", "Include a comprehensive data protection clause aligned with GDPR"],
                        "Similar_Contract_Analysis": "The contract aligns with 90% of industry standards but lacks specific details on data protection compared to similar contracts."
                    }

                    Please ensure the output is concise, detailed, and aligned with the structure above."""

        # Make Groq API call
        try:
            groq_client = GroqClient(GROQCLOUD_API_KEY)
            response = groq_client.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contract to analyze:\n{contract_text}\n\nSimilar contract:\n{similar_contract or 'No similar contract found'}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
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
                        "Compliance_Level": "Error",
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
                    "Compliance_Level": "Error",
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
                "Compliance_Level": "Error",
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

