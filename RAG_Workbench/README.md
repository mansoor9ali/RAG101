# RAG Workbench

A modern, full-stack Retrieval Augmented Generation (RAG) web application built with FastAPI and React. This application demonstrates various RAG techniques including basic semantic search, document reranking, query expansion, parent-child chunking, and advanced document parsing.

## Features

- **Basic RAG**: Upload PDFs and query them using semantic search with vector embeddings
- **Document Reranking**: Improve search results using cross-encoder models
- **Query Expansion**: Generate multiple related queries to improve retrieval
- **Parent-Child Chunking**: Advanced chunking strategy for better context retrieval
- **Document Parsing**: Convert PDFs to Markdown using Docling
- **Interactive UI**: Modern, responsive interface built with React and Tailwind CSS
- **Visualization**: View embeddings, chunks, and search results in real-time

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangChain**: LLM application framework
- **ChromaDB**: Vector database for embeddings
- **Sentence Transformers**: For text embeddings (BAAI/bge-small-en-v1.5)
- **DeepSeek**: LLM integration (chat and reasoning models)
- **PyMuPDF**: PDF processing
- **Docling**: Advanced document conversion

### Frontend
- **React 19**: UI framework
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animations
- **Axios**: HTTP client
- **React Router**: Navigation
- **Lucide React**: Icons

## Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 18 or higher
- **npm**: 9 or higher
 

## Installation

### 1. Clone the Repository

```bash
cd RAG101
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd RAG101
pip install -r requirements.txt
```

The backend requires:
- fastapi
- uvicorn
- python-multipart
- python-dotenv
- langchain
- langchain-community
- langchain-core
- langchain-text-splitters
- sentence-transformers
- chromadb
- PyMuPDF (fitz)
- docling

#### Additional Dependencies

You may need to install PyMuPDF separately if not included:
```bash
pip install PyMuPDF
```

For Docling (document conversion):
```bash
pip install docling
```

### 3. Frontend Setup

```bash
cd RAG101/frontend
npm install
```

## Environment Configuration

Create a `.env` file in the **root directory** (`/RAG101/RAG_Workbench/.env`):

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_KEY2=your_second_openai_api_key_here
OPENAI_BASE_URL=https://api.synthetic.new/openai/v1
OPENAI_MODEL_ID=hf:openai/gpt-oss-120b
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL_ID=deepseek-chat
RAG_PROJECT_ID=Test_Project_001

```

## Running the Application

### Development Mode

You need to run both the backend and frontend servers simultaneously.

#### Terminal 1: Start Backend Server

```bash
cd RAG101/backend
uvicorn main:app --reload --port 8000
```

The backend API will be available at: `http://localhost:8000`

You can verify it's running by visiting: `http://localhost:8000` (should show a welcome message)

API documentation is auto-generated at: `http://localhost:8000/docs`

#### Terminal 2: Start Frontend Dev Server

```bash
cd RAG101/frontend
npm run dev
```

The frontend will be available at: `http://localhost:5173`

### Production Build

#### Backend
```bash
cd RAG101/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd RAG101/frontend
npm run build
npm run preview
```

## Using the Application

### 1. Basic RAG Workflow

1. Navigate to the **Basic RAG** page (home page)
2. Upload a PDF document using the file upload component
3. Configure chunking parameters:
   - **Chunk Size**: Size of text chunks (default: 1000)
   - **Chunk Overlap**: Overlap between chunks (default: 200)
4. Click **Process Document** to create embeddings
5. Enter a query in the search box
6. Adjust **Top K** to control number of results
7. Click **Search** to retrieve relevant chunks
8. View results with scores and embeddings

### 2. Document Reranking

1. Navigate to the **Reranking** page
2. Upload and process a document
3. Perform an initial search
4. Click **Rerank Results** to apply cross-encoder reranking
5. Compare original and reranked results

### 3. Query Expansion

1. Navigate to the **Query Expansion** page
2. Upload and process a document
3. Enter a query
4. Click **Expand Query** to generate related queries
5. Search using expanded queries for better coverage

### 4. Parent-Child Chunking

1. Navigate to the **Parent-Child** page
2. Upload a document
3. Process using parent-child chunking strategy
4. Query to see both parent contexts and child chunks
5. View how larger context improves retrieval

### 5. Document Parsing

1. Navigate to the **Parsing** page
2. Upload a PDF
3. Click **Convert to Markdown**
4. View the structured markdown output

## API Endpoints

### File Management
- `POST /api/upload` - Upload a PDF file
  - Returns: `{file_path, filename}`

### Basic RAG
- `POST /api/process` - Process a document and create vector embeddings
  - Body: `{file_path, chunk_size, chunk_overlap}`
  - Returns: `{collection_name, num_chunks, preview_chunks, embedding_preview}`

- `POST /api/query` - Query the vector store
  - Body: `{query, collection_name, top_k}`
  - Returns: `{results[], query_embedding}`

### Advanced Features
- `POST /api/rerank` - Rerank search results
  - Body: `{query, initial_results[], top_k}`
  - Returns: `{results[], query_embedding}`

- `POST /api/expand` - Expand a query into multiple related queries
  - Body: `{query}`
  - Returns: `{queries[]}`

- `POST /api/generate` - Generate an answer from context chunks
  - Body: `{query, context_chunks[]}`
  - Returns: `{answer}`

- `POST /api/convert` - Convert PDF to Markdown
  - Body: `{file_path}`
  - Returns: `{markdown_content}`

### Parent-Child Chunking
- `POST /api/process_pc` - Create parent-child index
  - Body: `{file_path}`
  - Returns: `{collection_name, num_chunks, preview_chunks}`

- `POST /api/query_pc` - Query parent-child index
  - Body: `{query, collection_name, top_k}`
  - Returns: `{parents[], children[], query_embedding}`

## Project Structure

```
RAG101/
├── .env                         # Environment variables
└──RAG_Workbench/
    ├── README.MD                # This file
    ├── backend/
    │   ├── main.py              # FastAPI application & routes
    │   ├── rag_core.py          # Core RAG functionality
    │   ├── models.py            # Pydantic models
    │   ├── requirements.txt     # Python dependencies
    │   ├── verify_env.py        # Environment verification
    │   └── uploads/             # Uploaded PDF files
    └── frontend/
        ├── index.html           # HTML entry point
        ├── package.json         # Node dependencies
        ├── vite.config.js       # Vite configuration
        └── src/
            ├── App.jsx          # Main React component
            ├── main.jsx         # React entry point
            ├── index.css        # Global styles
            ├── components/      # React components
            │   ├── Layout.jsx
            │   ├── Sidebar.jsx
            │   ├── FileUpload.jsx
            │   └── ResultsDisplay.jsx
            └── pages/           # Page components
                ├── BasicRAG.jsx
                ├── Reranking.jsx
                ├── Expansion.jsx
                ├── ParentChild.jsx
                └── Parsing.jsx
```

## Features Breakdown

### Embedding Model
- **Model**: BAAI/bge-small-en-v1.5
- **Device**: Automatically selects MPS (Mac), CUDA (GPU), or CPU
- **Normalization**: L2 normalization enabled

### Reranking Model
- **Model**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **Purpose**: Re-scores initial retrieval results for better accuracy

### LLM
- **Model**: deepseek-chat
- **Temperature**: 0.2 for generation, 0.5 for expansion
- **Max Tokens**: 512 for answers, 128 for query expansion

### Vector Store
- **Database**: ChromaDB (local, persistent)
- **Search**: Cosine similarity with scores

## Troubleshooting

### Backend Won't Start

**Error**: Module not found
```bash
# Ensure you're in the backend directory
cd webinar_app/backend
# Reinstall dependencies
pip install -r requirements.txt
```

**Error**: Port already in use
```bash
# Change port
uvicorn main:app --reload --port 8001
```

### Frontend Won't Start

**Error**: Dependencies not installed
```bash
cd RAG101/frontend
rm -rf node_modules package-lock.json
npm install
```

### Environment Variables Not Loading

1. Ensure `.env` is in the **RAG_Workbench directory** (`RAG_Workbench/.env`), not in backend or frontend
2. Verify the path structure matches:
   ```
   RAG_Workbench/
   ├── .env
   └── backend/
       └── main.py
   ```
3. Check environment loading:
   ```bash
   cd RAG_Workbench/backend
   python verify_env.py
   ```

### LLM Features Not Working

- Verify deepseek credentials in `.env`
- Ensure you have access to models
- LLM features include: answer generation, query expansion

### CORS Errors

- Ensure backend is running on port 8000
- Frontend proxy is configured in `vite.config.js`
- Check browser console for specific CORS issues

### File Upload Issues

1. Check `RAG_Workbench/backend/uploads/` directory exists
2. Verify write permissions
3. Check file size limits (default: no limit, but server may impose one)

### Model Loading Issues

**First run may be slow** as models download:
- BGE embeddings: ~150MB
- Cross-encoder: ~90MB
- Models cache in `~/.cache/huggingface/`

## Performance Tips

1. **GPU Acceleration**: Install PyTorch with CUDA support for faster embeddings
2. **Chunk Size**: Smaller chunks (500-1000) for precise retrieval, larger (1500-2000) for more context
3. **Top K**: Start with 5, increase if results are not relevant
4. **Reranking**: Use on top 10-20 results for best speed/quality tradeoff

## Development

### Adding New Features

1. **Backend**: Add routes in `main.py`, logic in `rag_core.py`
2. **Frontend**: Create page in `src/pages/`, add route in `App.jsx`
3. **Models**: Define Pydantic models in `models.py`

### Testing Backend

```bash
# Test API endpoint
curl http://localhost:8000/

# View API docs
open http://localhost:8000/docs
```