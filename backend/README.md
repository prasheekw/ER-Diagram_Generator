# Phase 2: Human Language Parser Backend

This backend converts natural language descriptions into valid Mermaid.js ER diagram code using LLMs.

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file and add your API key(s):

```bash
cp .env.example .env
```

Then edit `.env` and add **at least one** of the following:

#### Option A: Google Gemini API (Recommended)
- Get a free API key at: https://aistudio.google.com/app/apikey
- Add to `.env`: `GEMINI_API_KEY=your_actual_key_here`

#### Option B: Groq API (Llama 3)
- Get a free API key at: https://console.groq.com/keys
- Add to `.env`: `GROQ_API_KEY=your_actual_key_here`

#### Option C: Ollama (Local, No API Key)
- Install from: https://ollama.ai
- Pull the model: `ollama pull llama3.2`
- Set in `.env`: `OLLAMA_ENABLED=true`

### 3. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### POST `/api/generate-from-text`

Convert natural language to Mermaid ER diagram code.

**Request:**
```json
{
  "text": "Create an ER diagram for a library system with books, authors, and borrowers"
}
```

**Response (Success):**
```json
{
  "success": true,
  "mermaid_code": "erDiagram\n    BOOK {\n        string title\n        string isbn PK\n    }\n    AUTHOR {\n        string name\n    }\n    BORROWER {\n        string name\n    }\n    AUTHOR ||--o{ BOOK : writes\n    BORROWER }o--o{ BOOK : borrows"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "No API configured. Please set GEMINI_API_KEY or GROQ_API_KEY in .env file."
}
```

### GET `/api/health`

Check which APIs are configured.

**Response:**
```json
{
  "status": "ok",
  "apis_available": ["Gemini"],
  "message": "Set API keys in .env file to enable more providers"
}
```

## How It Works

1. User types a natural language description in the frontend
2. Frontend sends POST request to `/api/generate-from-text`
3. Backend tries APIs in this order:
   - Google Gemini (if key is set)
   - Groq (if key is set)
   - Ollama (if enabled)
4. First successful API returns Mermaid code
5. Frontend renders the diagram and fills the code textarea

## Testing with curl

```bash
# Health check
curl http://localhost:5000/api/health

# Generate from text
curl -X POST http://localhost:5000/api/generate-from-text \
  -H "Content-Type: application/json" \
  -d '{"text": "A simple e-commerce system with customers, orders, and products"}'
```

## Troubleshooting

### "No API configured" error
- Make sure you've copied `.env.example` to `.env`
- Verify your API key is correctly pasted (no extra spaces)
- Restart the server after changing `.env`

### Gemini API errors
- Check your API key is valid
- Ensure you have internet connectivity
- Free tier has rate limits (~60 requests/minute)

### Groq API errors
- Check your API key is valid
- Free tier has rate limits
- Model availability may vary

### Ollama errors
- Ensure Ollama is running: `ollama serve`
- Pull the model first: `ollama pull llama3.2`
- Default URL is `http://localhost:11434`
