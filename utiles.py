import fitz  # PyMuPDF
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter
from langchain_community.vectorstores import Chroma
import uuid

def retrieve_context(query, retriever, remove_duplicates=True):
    """
    Retrieves documents relevant to a given query using the retriever.

    Parameters:
    - query: The search query as a string.
    - retriever: An instance of a Retriever class used to fetch documents.
    - remove_duplicates: If True, removes duplicate chunks based on page_content. Defaults to True.

    Returns:
    - A list of Document objects relevant to the query (with duplicates removed if requested).

    Note:
    - ChromaDB retrievers expect query string directly, not a dictionary.
    - This function handles both newer (invoke) and older (get_relevant_documents) API formats.
    """
    # For ChromaDB retrievers, invoke expects query string directly (not dict)
    # Try the modern invoke() method first
    try:
        retrieved_docs = retriever.invoke(query)
    except (TypeError, KeyError, AttributeError) as e:
        # Fallback: use get_relevant_documents for compatibility with older LangChain versions
        if hasattr(retriever, 'get_relevant_documents'):
            retrieved_docs = retriever.get_relevant_documents(query)
        else:
            # Last resort: re-raise the original error
            raise ValueError(f"Retriever does not support invoke() or get_relevant_documents(): {e}")

    # Remove duplicates if requested (based on content hash)
    if remove_duplicates and retrieved_docs:
        seen_content = set()
        unique_docs = []

        for doc in retrieved_docs:
            # Use hash of page_content as unique identifier
            content_hash = hash(doc.page_content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)

        if len(unique_docs) < len(retrieved_docs):
            print(f"Removed {len(retrieved_docs) - len(unique_docs)} duplicate chunk(s)")

        return unique_docs

    return retrieved_docs

def get_retriever2(docs, embedding_model, collection_name="test", top_k=10):
    """
    Initializes a retriever object to fetch the top_k most relevant documents based on cosine similarity.

    Parameters:
    - docs: A list of documents to be indexed and retrieved.
    - embedding_model: The embedding model to use for generating document embeddings.
    - top_k: The number of top relevant documents to retrieve. Defaults to 3.

    Returns:
    - A retriever object configured to retrieve the top_k relevant documents.

    Raises:
    - ValueError: If any input parameter is invalid.
    """
    # Example of parameter validation (optional)
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    try:
        vector_store = Chroma.from_documents(
            docs,
            embedding_model,
            collection_name=collection_name
        )

        retriever = vector_store.as_retriever(k=top_k)
        # retriever.k = top_k

        return retriever
    except Exception as e:
        print(f"An error occurred while initializing the retriever: {e}")
        raise

def get_retriever(docs, embedding_model, top_k=5, collection_name=None):
    """
    Initializes a retriever object to fetch the top_k most relevant documents based on cosine similarity.

    Parameters:
    - docs: A list of documents to be indexed and retrieved.
    - embedding_model: The embedding model to use for generating document embeddings.
    - top_k: The number of top relevant documents to retrieve. Defaults to 3.
    - collection_name: (Optional) Unique name for ChromaDB collection. If None, generates a unique name.

    Returns:
    - A retriever object configured to retrieve the top_k relevant documents.

    Raises:
    - ValueError: If any input parameter is invalid.
    """
    # Example of parameter validation (optional)
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    try:
        # Use unique collection name to prevent duplicates
        if collection_name is None:
            collection_name = f"rag_collection_{uuid.uuid4().hex[:8]}"

        vector_store = Chroma.from_documents(
                docs,
                embedding_model,
                collection_name=collection_name
            )

        retriever = vector_store.as_retriever(k=top_k)
        # retriever.k = top_k

        return retriever
    except Exception as e:
        print(f"An error occurred while initializing the retriever: {e}")
        raise

def load_pdf_docling(files="data/2306.02707.pdf"):
    """
    Loads documents from PDF files using Docling (structure-preserving parser).

    Parameters:
    - files: A string representing a single file path or a list of strings representing multiple file paths.

    Returns:
    - A list of Document objects loaded from the provided PDF files with structure preserved.

    Raises:
    - FileNotFoundError: If any of the provided file paths do not exist.
    - Exception: For any other issues encountered during file loading.
    """
    if not isinstance(files, list):
        files = [files]  # Ensure 'files' is always a list

    documents = []
    converter = DocumentConverter()

    for file_path in files:
        try:
            print(f"Converting {file_path} with Docling...")
            result = converter.convert(file_path)
            markdown_output = result.document.export_to_markdown()

            # Create a Document object
            document = Document(
                page_content=markdown_output,
                metadata={
                    "source": file_path,
                    "parser": "docling",
                    "num_pages": len(result.document.pages),
                    "num_tables": len(result.document.tables),
                    "structure_preserved": True
                }
            )
            documents.append(document)
            print(f"✅ Successfully converted {file_path}")
        except FileNotFoundError as e:
            print(f"File not found: {file_path}")
            raise
        except Exception as e:
            print(f"An error occurred while loading {file_path}: {e}")
            raise

    return documents

def load_pdf(files="data/2306.02707.pdf"):
    """
    Loads documents from PDF files using PyMuPDF.

    Parameters:
    - files: A string representing a single file path or a list of strings representing multiple file paths.

    Returns:
    - A list of Document objects loaded from the provided PDF files.

    Raises:
    - FileNotFoundError: If any of the provided file paths do not exist.
    - Exception: For any other issues encountered during file loading.

    The function applies post-processing steps such as cleaning extra whitespace and grouping broken paragraphs.
    """
    if not isinstance(files, list):
        files = [files]  # Ensure 'files' is always a list

    documents = []
    for file_path in files:
        try:
            # Open the PDF file
            doc = fitz.open(file_path)
            text = ""
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text")

            # Apply post-processing steps
            text = clean_extra_whitespace(text)
            text = group_broken_paragraphs(text)

            # Create a Document object
            document = Document(
                page_content=text,
                metadata={"source": file_path}
            )
            documents.append(document)
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
            raise
        except Exception as e:
            print(f"An error occurred while loading {file_path}: {e}")
            raise

    return documents

def clean_extra_whitespace(text):
    """
    Cleans extra whitespace from the provided text.

    Parameters:
    - text: A string representing the text to be cleaned.

    Returns:
    - A string with extra whitespace removed.
    """
    return ' '.join(text.split())

def group_broken_paragraphs(text):
    """
    Groups broken paragraphs in the provided text.

    Parameters:
    - text: A string representing the text to be processed.

    Returns:
    - A string with broken paragraphs grouped.
    """
    return text.replace("\n", " ").replace("\r", " ")
