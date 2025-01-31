from groq import Groq

class LLMService:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
    
    def analyze_key_clauses(self, text):
        # Existing GroqClient logic for key clause extraction
        pass

    def analyze_contract(self, contract_text, similar_contract):
        # Existing GroqClient logic for contract analysis
        pass 