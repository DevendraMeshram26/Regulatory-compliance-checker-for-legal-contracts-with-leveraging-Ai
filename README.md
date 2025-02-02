# Regulatory Compliance Checker

## Overview
The **Regulatory Compliance Checker** is an AI-powered tool designed to analyze legal documents for compliance, risks, and recommendations. It leverages **FastAPI** for backend processing, **Streamlit** for an interactive UI, **Chromadb** for document storage and retrieval, and **Groq's LLM API** for AI-driven analysis. Additionally, **Slack service** is integrated to send notifications about application events.

## Features
- **Document Upload:** Supports **PDF, TXT, DOCX** formats.
- **Clause Extraction:** Identifies key clauses within legal documents.
- **Similarity Search:** Compares uploaded documents with a dataset stored in **Chromadb**.
- **Compliance Analysis:** Uses **LLM** to assess legal risks and provide recommendations.
- **User-Friendly Interface:** Built with **Streamlit** for easy interaction.
- **Slack Notifications:** Sends alerts and updates via **Slack** for user engagement.
- **Secure & Scalable:** Implements best practices for **data privacy and deployment**.

## Technology Stack
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Database:** Chromadb
- **AI/LLM:** Groq Cloud API
- **Notifications:** Slack API
- **Deployment:** CI/CD pipeline, Cloud hosting

## Installation & Setup
### Prerequisites
- Python 3.8+
- Pip package manager
- Virtual environment (optional but recommended)
- Slack Webhook URL for notifications

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/regulatory-compliance-checker.git
   cd regulatory-compliance-checker
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up Slack Webhook URL in environment variables:
   ```bash
   export SLACK_WEBHOOK_URL='your-webhook-url'
   ```
5. Run the backend (FastAPI):
   ```bash
   uvicorn main:app --reload
   ```
6. Run the frontend (Streamlit):
   ```bash
   streamlit run app.py
   ```

## Usage
1. Upload a legal document.
2. The tool extracts key clauses and identifies relevant contract sections.
3. It searches for similar documents in **Chromadb**.
4. The **LLM** analyzes both documents and generates a compliance report.
5. Users receive insights on legal risks, compliance levels, and recommendations.
6. Notifications about document analysis and compliance status are sent via **Slack**.

## Future Enhancements
- Expand dataset with global regulatory standards.
- Implement multi-language support.
- Real-time compliance updates.
- Advanced Slack notifications with interactive actions.

## Contributors
- **Devendra Meshram** – AI & Full-Stack Developer
- **Other Contributors**

## License
This project is licensed under the MIT License.

---

For any questions or contributions, feel free to open an issue or submit a pull request!

