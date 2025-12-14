"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import ingest, query, chunks, pdf


app = FastAPI(
    title="Catan Rules Q&A API",
    description="API for querying Catan board game rules with verified citations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(chunks.router)
app.include_router(pdf.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Catan Rules Q&A API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

