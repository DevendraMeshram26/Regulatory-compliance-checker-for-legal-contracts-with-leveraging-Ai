import streamlit as st
import requests
import json
from io import BytesIO

def main():
    st.title("Regulatory Compliance Checker")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Contract (PDF, DOCX, or TXT)", 
                                   type=['pdf', 'docx', 'txt'])
    
    if uploaded_file:
        # Display file details
        st.write(f"Uploaded file: {uploaded_file.name}")
        
        # Create file object to send to backend
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        
        try:
            # Send file to backend for key clause extraction
            response = requests.post("http://localhost:8000/uploadfile/", files=files)
            
            if response.status_code == 200:
                result = response.json()
                
                # Display Key Clauses
                # st.markdown("---")
                st.subheader("Key Clauses")
                for clause in result.get("clauses", []):
                    with st.expander(clause["clause"]):
                        st.write(clause["description"])
                
                # Display Analysis Results
                st.markdown("---")
                # Directly analyze contract
                analysis_response = requests.post(
                    "http://localhost:8000/analyze/",
                    json={"clauses": result["clauses"]}
                )
                
                if analysis_response.status_code == 200:
                    analysis_result = analysis_response.json()
                    
                    st.subheader("Contract Analysis Results")
                    
                    # Display Score and Compliance Level in two columns with reasoning
                    score_col, compliance_col = st.columns(2)
                    
                    with score_col:
                        st.metric("Contract Score", f"{analysis_result.get('Score', 0)}/100")
                        if score_reasoning := analysis_result.get('Score_Reasoning'):
                            st.markdown(f"*{score_reasoning}*")
                    
                    with compliance_col:
                        st.metric("Compliance Level", analysis_result.get('Compliance_Level', 'N/A'))
                        if compliance_reasoning := analysis_result.get('Compliance_Reasoning'):
                            st.markdown(f"*{compliance_reasoning}*")
                    
                    # Display Strengths
                    with st.expander("Contract Strengths"):
                        strengths = analysis_result.get('Strengths', [])
                        if strengths:
                            for strength in strengths:
                                st.success(strength)
                        else:
                            st.info("No strengths identified")
                    
                    # Display Improvement Areas
                    with st.expander("Areas for Improvement"):
                        improvements = analysis_result.get('Improvement_Areas', [])
                        if improvements:
                            for area in improvements:
                                st.warning(area)
                        else:
                            st.info("No improvement areas identified")
                    
                    # Display Legal Risks
                    with st.expander("Legal Risks"):
                        risks = analysis_result.get('Legal_Risks', [])
                        if risks:
                            for risk in risks:
                                st.error(risk)
                        else:
                            st.info("No legal risks identified")
                    
                    # Display Recommendations
                    with st.expander("Recommendations"):
                        recommendations = analysis_result.get('Recommendations', [])
                        if recommendations:
                            for rec in recommendations:
                                st.info(rec)
                        else:
                            st.info("No recommendations provided")
                    
                    # Display Similar Contract Analysis
                    with st.expander("Similar Contract Analysis"):
                        similar_analysis = analysis_result.get('Similar_Contract_Analysis')
                        if similar_analysis and similar_analysis != "Analysis failed":
                            st.write(similar_analysis)
                        else:
                            st.info("No similar contract analysis available")
                else:
                    st.error("Error analyzing contract")
            else:
                st.error("Error processing file")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 