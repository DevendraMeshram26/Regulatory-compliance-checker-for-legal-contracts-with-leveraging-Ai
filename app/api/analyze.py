from fastapi import APIRouter
from fastapi.responses import JSONResponse
# from app.services.groq_service import analyze_contract
# from app.services.chroma_service import retrieve_similar_contract
from app.utils.logger import logger
from app.services.chroma_service import chroma_client
import json
from config import Config
from app.services.groq_client import GroqClient
router = APIRouter()

@router.post("/analyze/")
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

        # Make Groq API call
        try:
            groq_client = GroqClient(Config.GROQCLOUD_API_KEY)
            response = groq_client.client.chat.completions.create(
                model="llama-3.2-3b-preview",
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
                logger.error(f"JSON parsing error: {json_err} - Response content: {response_content}")
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
            logger.error(f"Error calling Groq API: {api_err}")
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
        logger.error(f"General error in analyze_contract: {e}")
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