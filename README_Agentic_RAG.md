# Qwen Agentic RAG (Streamlit)

An interactive Retrieval-Augmented Generation (RAG) demo that integrates local Ollama-served LLMs (Qwen / DeepSeek) with document ingestion, FAISS vector search, reasoning trace display, and a weather tool powered by the Amap (Gaode) API — all wrapped in a Streamlit UI.

## 🚀 Key Features
- **Multi-Model Support**: Switch between `qwen3:1.7b`, `deepseek-r1:1.5b`, `qwen3:8b` at runtime.
- **Embeddings Flexibility**: Choose among several embedding models (e.g. `bge-m3:latest`, `nomic-embed-text:latest`).
- **Document RAG Pipeline**: Upload PDF / TXT, automatic chunking (LangChain splitter) and indexing via FAISS.
- **Incremental Indexing**: Add new documents without full rebuild.
- **Reasoning Visibility**: `<think>...</think>` segments collapsed in UI (expand to inspect chain-of-thought style reasoning output from reasoning-capable models).
- **Weather Tool Integration**: Real-time city weather lookup using Amap API.
- **Chat History Persistence**: Stores conversation + retrieved document chunks to `chat_history.json`.
- **CSV Export**: Download past conversation turns.

## 🧱 Architecture Overview
```
Streamlit UI (app.py)
 ├── Sidebar Controls (model, embedding, RAG toggle, threshold)
 ├── Document Upload + Processing (utils/document_processor.py)
 ├── Vector Store Service (services/vector_store.py – FAISS + OllamaEmbeddings)
 ├── Agent Layer (models/agent.py – agno.Agent + tools)
 │    ├── Weather Tool (services/weather_tools.py)
 │    └── Reasoning Tools (agno.tools.reasoning)
 ├── Chat History (utils/chat_history.py)
 └── UI Rendering (utils/ui_components.py)
```

## 📂 Directory Structure
```
.
├── app.py
├── requirements.txt
├── config/
│   └── settings.py
├── models/
│   └── agent.py
├── services/
│   ├── vector_store.py
│   └── weather_tools.py
├── utils/
│   ├── chat_history.py
│   ├── document_processor.py
│   ├── ui_components.py
│   └── decorators.py
├── faiss_index/        # (Ignored) Generated FAISS index files
├── chat_history.json   # (Ignored) Conversation persistence
└── README.md
```

## ⚙️ Configuration
All main tunables live in `config/settings.py`:
- `DEFAULT_MODEL`, `AVAILABLE_MODELS`
- `EMBEDDING_MODEL`, `AVAILABLE_EMBEDDING_MODELS`, `EMBEDDING_BASE_URL`
- Chunking: `CHUNK_SIZE`, `CHUNK_OVERLAP`, `SEPARATORS`
- Retrieval: `DEFAULT_SIMILARITY_THRESHOLD`, `MAX_RETRIEVED_DOCS`
- Weather: `AMAP_API_KEY`
- History: `MAX_HISTORY_TURNS`

### 🔐 Environment / Secrets
Currently the Amap API key is hard-coded. Recommended improvement: move it to an environment variable, e.g. `AMAP_API_KEY` loaded via `os.getenv` and supply a `.env` / `example.env` file.

## 🛠 Prerequisites
- **Python** 3.11+ (project appears 3.12-compatible from pyc bytecode)
- **Ollama** running locally with required models pulled:
  ```bash
  ollama pull qwen3:8b
  ollama pull qwen3:1.7b
  ollama pull deepseek-r1:1.5b
  ollama pull bge-m3:latest
  ollama pull nomic-embed-text:latest
  ```
- (Optional) Other embedding models per `AVAILABLE_EMBEDDING_MODELS`.

## 📦 Install Dependencies
```bash
pip install -r requirements.txt
```
If you use a virtual environment (recommended):
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

## ▶️ Run the App
Primary run command (as requested):
```bash
streamlit run run_agentic_rag.py --server.port 6006
```
Then open: http://localhost:6006

## 🧪 Usage Flow
1. Start Ollama in background (if not already).
2. Run the Streamlit app.
3. In sidebar: pick a base model + embedding model.
4. Upload PDFs / TXT files and click "Process documents".
5. Ask a question related to the documents (RAG mode on) or toggle RAG off for pure chat.
6. Ask weather: "What's the weather in Shenzhen?" → the agent calls the weather tool.
7. Expand reasoning blocks to inspect `<think>` segments.
8. Export or clear history from the sidebar.

## 📁 Document Processing Details
- PDF loader: `PyPDFLoader` (LangChain community)
- Splitting: `RecursiveCharacterTextSplitter` with hierarchical separators.
- Caching: Hash-based cache per PDF in `.cache/` (retains splits across runs).
- Vector store: FAISS local, saved under `faiss_index/`.
- Search: similarity + post-filter by score threshold.

## 🧩 Agent & Tooling
- Framework: `agno` Agent (with `Ollama` model wrapper).
- Tools:
  - `ReasoningTools`: adds reasoning instructions.
  - Weather tool (Amap API) as a structured function call.
- Prompt strategy: If context provided → user question + retrieved content; else pure question.

## 🗃 Chat History
- Stored JSON: `chat_history.json` (ignored by git).
- Roles used: `user`, `assistant`, `assistant_think`, `retrieved_doc`.
- Export: CSV via `pandas`.

## 🔍 Troubleshooting
| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` (e.g. `agno`) | Missing dependency | Re-run `pip install -r requirements.txt` |
| Embedding model mismatch / no vectors | Not processed after switching embedding model | Re-upload and re-process documents |
| Empty retrieval results | High similarity threshold | Lower threshold slider (e.g. 0.5) |
| Weather always fails | Invalid Amap API key | Obtain key & update settings / env |
| Streamlit port busy | Port 6006 in use | Run with `--server.port 6010` |
| No reasoning block shown | Model lacks reasoning output | Switch to a reasoning-capable model (`deepseek-r1:1.5b`) |

## ♻️ Clearing State
- Clear documents: "Clear all documents" button (removes FAISS index files).
- Clear chat: Sidebar "Clear conversation".
- Clear cache: Manually delete `.cache/*.json` (or add a helper function).

## 🧪 Suggested Enhancements (Roadmap)
- Move secrets to env + add `example.env`.
- Add automated tests (unit + integration for vector store and agent prompt assembly).
- Add Dockerfile (Ollama + app orchestration with compose).
- Provide offline embedding fallback check.
- Pre-commit hooks: `ruff`, `black`, `isort`.
- Add usage analytics / basic telemetry toggle.
- Multi-file type support (DOCX / Markdown loaders).
- Add UI for incremental doc addition (already have backend method `add_document`).

## 🔒 License
Add a LICENSE file appropriate for your distribution (MIT recommended if open-sourcing).

## 🙋 Support / Questions
Open an issue or start a discussion once the repo is published.

---
Happy building! 🐋
