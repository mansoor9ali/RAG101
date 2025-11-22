from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import traceback
from typing import List
from dotenv import load_dotenv

# Load environment variables from the root directory
# main.py is in /backend
# dirname -> /backend
# dirname -> /webinar_app
# dirname -> /YT (where .env is)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

from rag_core import load_pdf, split_text, create_vector_store, retrieve_documents, rerank_documents, convert_to_markdown, generate_answer, expand_query, create_parent_child_index, retrieve_parent_child, get_text_embedding
from models import ProcessRequest, ProcessResponse, QueryRequest, QueryResponse, SearchResult, RerankRequest, RerankResponse, ConversionResponse, GenerateRequest, GenerateResponse, ExpansionRequest, ExpansionResponse, ParentChildResponse
from langchain_core.documents import Document

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/process_pc", response_model=ProcessResponse)
async def process_parent_child(request: ProcessRequest):
    try:
        docs = load_pdf(request.file_path)
        collection_name = create_parent_child_index(docs)
        return ProcessResponse(
            collection_name=collection_name,
            num_chunks=0, # Not easily countable here
            preview_chunks=["Parent-Child Index Created"]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query_pc", response_model=ParentChildResponse)
async def query_parent_child(request: QueryRequest):
    try:
        query_embedding = get_text_embedding(request.query)
        parents, children = retrieve_parent_child(request.query, request.collection_name, request.top_k)
        
        formatted_parents = [SearchResult(content=p.page_content, score=1.0, metadata=p.metadata) for p in parents]
        formatted_children = [SearchResult(content=c[0].page_content, score=c[1], metadata=c[0].metadata) for c in children]
        
        return ParentChildResponse(parents=formatted_parents, children=formatted_children, query_embedding=query_embedding)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expand", response_model=ExpansionResponse)
async def expand_query_endpoint(request: ExpansionRequest):
    try:
        queries = expand_query(request.query)
        return ExpansionResponse(queries=queries)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_response(request: GenerateRequest):
    try:
        answer = generate_answer(request.query, request.context_chunks)
        return GenerateResponse(answer=answer)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/convert", response_model=ConversionResponse)
async def convert_document(request: ProcessRequest):
    try:
        markdown = convert_to_markdown(request.file_path)
        return ConversionResponse(markdown_content=markdown)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rerank", response_model=RerankResponse)
async def rerank_results(request: RerankRequest):
    try:
        query_embedding = get_text_embedding(request.query)
        # Reconstruct Document objects from input
        docs = []
        for res in request.initial_results:
            docs.append(Document(page_content=res.content, metadata=res.metadata))
            
        reranked = rerank_documents(request.query, docs, request.top_k)
        
        formatted_results = []
        for doc, score in reranked:
            formatted_results.append(SearchResult(
                content=doc.page_content,
                score=float(score), # Ensure float for JSON serialization
                metadata=doc.metadata,
                embedding=get_text_embedding(doc.page_content)
            ))
            
        return RerankResponse(results=formatted_results, query_embedding=query_embedding)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "RAG Webinar API is running"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"file_path": file_path, "filename": file.filename}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest):
    try:
        # 1. Load PDF
        docs = load_pdf(request.file_path)
        
        # 2. Split Text
        chunks = split_text(docs, chunk_size=request.chunk_size, chunk_overlap=request.chunk_overlap)
        
        # 3. Create Vector Store
        vector_store, collection_name = create_vector_store(chunks)
        
        # Prepare preview
        preview = [chunk.page_content[:200] + "..." for chunk in chunks[:3]]
        embedding_preview = get_text_embedding(chunks[0].page_content) if chunks else None
        
        return ProcessResponse(
            collection_name=collection_name,
            num_chunks=len(chunks),
            preview_chunks=preview,
            embedding_preview=embedding_preview
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    try:
        query_embedding = get_text_embedding(request.query)
        results = retrieve_documents(request.query, request.collection_name, request.top_k)
        
        # Format results (Chroma returns (doc, score) tuples)
        formatted_results = []
        for doc, score in results:
            formatted_results.append(SearchResult(
                content=doc.page_content,
                score=score,
                metadata=doc.metadata,
                embedding=get_text_embedding(doc.page_content)
            ))
            
        return QueryResponse(results=formatted_results, query_embedding=query_embedding)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
