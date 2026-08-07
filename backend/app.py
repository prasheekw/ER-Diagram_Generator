"""
Phase 2: Human Language Parser Backend
Flask API that converts natural language descriptions to Mermaid.js ER diagram code.

API Priority (tried in order):
1. Google Gemini API (free tier available)
2. Groq API (Llama 3, free tier available)
3. Ollama (local, no API key needed)
"""

import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
OLLAMA_ENABLED = os.getenv('OLLAMA_ENABLED', 'false').lower() == 'true'
OLLAMA_URL = 'http://localhost:11434'

# System prompt for consistent Mermaid ER diagram generation
SYSTEM_PROMPT = """You are an expert at creating Mermaid.js ER diagrams. 
Your task is to convert natural language descriptions into valid Mermaid ER diagram syntax.

RULES:
1. ONLY output the Mermaid code inside a code block with ```mermaid tags
2. Use proper Mermaid ER syntax:
   - Entities: erDiagram ENTITY_NAME { type field_name "description" }
   - Relationships: ENTITY_A ||--o{ ENTITY_B : relationship_type
   - Types: string, int, float, date, boolean
   - Keys: PK for primary key, FK for foreign key
3. Include all entities, attributes, and relationships mentioned
4. Make reasonable assumptions for missing details
5. Do NOT include any explanation text outside the code block
6. The output must be parseable by mermaid.js

Example output format:
```mermaid
erDiagram
    CUSTOMER {
        string name PK
        string email
        int age
    }
    ORDER {
        int id PK
        date order_date
        float total
    }
    CUSTOMER ||--o{ ORDER : places
```

Now convert the following description into Mermaid ER diagram code:"""


def extract_mermaid_code(text):
    """Extract Mermaid code from LLM response, handling various formats."""
    # Try to find code block with mermaid tag
    pattern = r'```mermaid\s*(.*?)\s*```'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback: try any code block
    pattern = r'```\s*(.*?)\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        # Remove 'erDiagram' if it appears as first line separately
        if content.startswith('erDiagram'):
            return content
        return content
    
    # Last resort: return the whole text if it looks like mermaid code
    if 'erDiagram' in text or '--' in text:
        return text.strip()
    
    return text.strip()


def call_gemini_api(user_text):
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\n{user_text}")
        
        return extract_mermaid_code(response.text)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def call_groq_api(user_text):
    """Call Groq API (Llama 3)."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.2-90b-text-preview",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return extract_mermaid_code(completion.choices[0].message.content)
    except Exception as e:
        print(f"Groq API error: {e}")
        return None


def call_ollama_api(user_text):
    """Call local Ollama API."""
    try:
        import requests
        
        payload = {
            "model": "llama3.2",
            "prompt": f"{SYSTEM_PROMPT}\n\n{user_text}",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2000
            }
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return extract_mermaid_code(result.get('response', ''))
    except Exception as e:
        print(f"Ollama API error: {e}")
        return None


def generate_mermaid_code(user_text):
    """
    Try available APIs in priority order to generate Mermaid code.
    Returns: (success: bool, mermaid_code: str or error_message: str)
    """
    # Try Gemini first
    if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here':
        print("Trying Gemini API...")
        result = call_gemini_api(user_text)
        if result:
            return True, result
    
    # Try Groq second
    if GROQ_API_KEY and GROQ_API_KEY != 'your_groq_api_key_here':
        print("Trying Groq API...")
        result = call_groq_api(user_text)
        if result:
            return True, result
    
    # Try Ollama last (local)
    if OLLAMA_ENABLED:
        print("Trying Ollama API...")
        result = call_ollama_api(user_text)
        if result:
            return True, result
    
    # No API available
    error_msg = "No API configured. Please set GEMINI_API_KEY or GROQ_API_KEY in .env file, or enable Ollama."
    print(error_msg)
    return False, error_msg


@app.route('/api/generate-from-text', methods=['POST'])
def generate_from_text():
    """
    Endpoint to convert natural language to Mermaid ER diagram code.
    
    Request JSON:
        { "text": "user description of the ER diagram" }
    
    Response JSON:
        { 
            "success": true/false,
            "mermaid_code": "...",  // if success
            "error": "..."          // if failed
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing "text" field in request body'
            }), 400
        
        user_text = data['text'].strip()
        
        if not user_text:
            return jsonify({
                'success': False,
                'error': 'Text field cannot be empty'
            }), 400
        
        print(f"Received request: {user_text[:100]}...")
        
        success, result = generate_mermaid_code(user_text)
        
        if success:
            print("Successfully generated Mermaid code")
            return jsonify({
                'success': True,
                'mermaid_code': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 503
            
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    apis_available = []
    if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here':
        apis_available.append('Gemini')
    if GROQ_API_KEY and GROQ_API_KEY != 'your_groq_api_key_here':
        apis_available.append('Groq')
    if OLLAMA_ENABLED:
        apis_available.append('Ollama')
    
    return jsonify({
        'status': 'ok',
        'apis_available': apis_available,
        'message': 'Set API keys in .env file to enable more providers'
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Phase 2: Human Language Parser Backend")
    print("=" * 60)
    print("\nAvailable APIs:")
    if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here':
        print("  ✓ Gemini API configured")
    else:
        print("  ✗ Gemini API not configured (set GEMINI_API_KEY in .env)")
    
    if GROQ_API_KEY and GROQ_API_KEY != 'your_groq_api_key_here':
        print("  ✓ Groq API configured")
    else:
        print("  ✗ Groq API not configured (set GROQ_API_KEY in .env)")
    
    if OLLAMA_ENABLED:
        print("  ✓ Ollama enabled (local)")
    else:
        print("  ✗ Ollama not enabled (set OLLAMA_ENABLED=true in .env)")
    
    print("\nStarting server on http://localhost:5000")
    print("Test endpoint: POST /api/generate-from-text")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
