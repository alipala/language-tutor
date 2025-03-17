from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from backend.rag.dutch_tutor_rag import DutchTutorRAG

router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
)

class QueryRequest(BaseModel):
    query: str
    language: str = "dutch"
    level: str = "B1"

# Initialize RAG system
rag_system = DutchTutorRAG()

@router.post("/query")
async def query_with_context(request: QueryRequest):
    """Process a user query with context from the RAG system."""
    try:
        result = rag_system.query_with_context(
            user_query=request.query,
            language=request.language,
            level=request.level
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/update")
async def update_vector_database(background_tasks: BackgroundTasks):
    """Run the RAG update in the background."""
    try:
        background_tasks.add_task(rag_system.update_vector_database)
        return {"status": "update_started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting update: {str(e)}")
