from groq import Groq

class GroqClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
    
#     def analyze_contract(self, contract_text, similar_contract, system_prompt):
#         messages = [
#             {
#                 "role": "system",
#                 "content": system_prompt
#             },
#             {
#                 "role": "user",
#                 "content": f"""Please analyze the following contract and compare it with a similar contract:

# Current Contract:
# {contract_text}

# Similar Contract for Reference:
# {similar_contract}

# Please provide:
# 1. Any regulatory compliance issues
# 2. Recommendations for improvements
# 3. Notable differences from the similar contract"""
#             }
#         ]
        
#         response = self.client.chat.completions.create(
#             model="llama3-8b-8192",
#             messages=messages,
#             temperature=0.3,
#             max_tokens=2000
#         )
        
#         return response.choices[0].message.content

#     def extract_key_clauses(self, text):
#         messages = [
#             {
#                 "role": "system",
#                 "content": """Extract key clauses from the contract and return them in JSON format:
#                 {
#                     "clauses": [
#                         {
#                             "clause": "<clause title>",
#                             "description": "<clause description>"
#                         }
#                     ]
#                 }"""
#             },
#             {
#                 "role": "user",
#                 "content": text
#             }
#         ]
        
#         response = self.client.chat.completions.create(
#             model="llama3-8b-8192",
#             messages=messages,
#             temperature=0
#         )
        
#         return response.choices[0].message.content

#     def generate_response(self, prompt):
#         # Add your Groq interaction logic here
#         pass 