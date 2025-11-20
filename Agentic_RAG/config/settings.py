"""
Configuration file containing all constants and settings.
"""

# 1. File paths
VECTOR_STORE_PATH = "faiss_index"
HISTORY_FILE = "chat_history.json"

# 2. Model configuration
DEFAULT_MODEL = "qwen3:8b"
AVAILABLE_MODELS = ["qwen3:1.7b", "deepseek-r1:1.5b", "qwen3:8b"]

EMBEDDING_MODEL = "bge-m3:latest"
AVAILABLE_EMBEDDING_MODELS = ["bge-m3:latest", "nomic-embed-text:latest", "mxbai-embed-large:latest", "bge-large-en-v1.5:latest", "bge-large-zh-v1.5:latest"]
EMBEDDING_BASE_URL = "http://localhost:11434"


# 3. RAG configuration
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_CHUNK_SIZE = 300
DEFAULT_CHUNK_OVERLAP = 30
MAX_RETRIEVED_DOCS = 3

# 4. Amap (Gaode) API configuration
AMAP_API_KEY = "48257ed7b33d55e349260a9837436968" 

# 5. LangChain configuration
CHUNK_SIZE = 300
CHUNK_OVERLAP = 30
SEPARATORS = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]

# 6. Chat history configuration
MAX_HISTORY_TURNS = 5 