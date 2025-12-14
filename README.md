# Catan Rules Q&A App

A production-ready application for querying Catan board game rules with verified citations. Built with FastAPI backend and Next.js frontend, using LangChain for RAG orchestration, Chroma for vector storage, and react-pdf for PDF viewing with exact text highlights.

## Features

- **Natural Language Q&A**: Ask questions about Catan rules in plain English
- **Verified Citations**: Every answer includes verbatim quotes from official rulebooks
- **PDF Viewer with Highlights**: View the exact source in the PDF with highlighted text
- **Hallucination Control**: Answers are tied directly to textual evidence from rulebooks

## Architecture

- **Backend**: FastAPI (Python) with LangChain for RAG
- **Frontend**: Next.js (TypeScript/React) with react-pdf
- **Vector Store**: Chroma (via LangChain)
- **LLM**: Support for both OpenAI and Google Vertex AI (configurable)
- **PDF Processing**: Custom pipeline using PyMuPDF for coordinate tracking

## Project Structure

```
catan-adjudicator/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── data/            # PDF rulebooks
└── README.md
```

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Configure your `.env` file with:
   - `LLM_PROVIDER`: "openai" or "vertex"
   - `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to credentials (if using Vertex)
   - `VERTEX_PROJECT_ID`: Your GCP project ID (if using Vertex)
   - `CHROMA_PERSIST_DIR`: Directory for Chroma database (default: ./chroma_db)

6. Run the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the frontend:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

## Usage

### Ingesting PDFs

1. Use the `/api/ingest` endpoint to upload PDF rulebooks:
```bash
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@data/CN3081 CATAN–The Game Rulebook secure (1).pdf"
```

2. The system will:
   - Parse the PDF with coordinate tracking
   - Chunk the text into semantic units
   - Generate embeddings
   - Store in the vector database

### Querying

1. Open the frontend at `http://localhost:3000`
2. Enter a question about Catan rules
3. View the answer with source citations
4. Click on sources to view them in the PDF viewer with highlights

## API Endpoints

- `POST /api/ingest`: Upload and ingest a PDF file
- `POST /api/query`: Ask a question about Catan rules
- `GET /api/chunks/{chunk_id}`: Retrieve full chunk details with atoms

## Development

### Backend Development

The backend uses FastAPI with automatic API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Development

The frontend uses Next.js with:
- TypeScript for type safety
- TailwindCSS for styling
- react-pdf for PDF rendering

## License

MIT

