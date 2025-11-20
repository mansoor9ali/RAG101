import os

from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from rich import print

from embeddingsUtiles import load_embedding_model
from utiles import load_pdf, get_retriever, retrieve_context

load_dotenv()

if __name__ == '__main__':
    print('Starting Simple RAG example...')
    if not os.path.exists("./data"):
        os.mkdir("./data")

    try:
        from docling.document_converter import DocumentConverter

        print("✅ Docling installed successfully!")
    except ImportError as e:
        print(f"⚠️ Installation issue: {e}")
        print("If you see NumPy compatibility errors, restart the runtime and run this cell again.")

    data = load_pdf()
    print(data[0].page_content[:5000])

    # Create converter
    converter = DocumentConverter()

    # Convert our downloaded PDF
    print("Converting PDF with Docling...")
    print("This may take 30-60 seconds for a ~50 page document...")

    result = converter.convert("./data/2306.02707.pdf")

    print(f"✅ Conversion complete!")
    print(f"Document has {len(result.document.pages)} pages")

    #============================================
    # SECTION 1.2: Splitting Documents into Chunks
    # ============================================

    # Export to markdown
    markdown_output = result.document.export_to_markdown()

    # Create a Document object from Docling output
    docling_document = Document(
        page_content=markdown_output,
        metadata={
            "source": "./data/2306.02707.pdf",
            "parser": "docling",
            "num_pages": len(result.document.pages),
            "num_tables": len(result.document.tables),
            "structure_preserved": True
        }
    )

    print("✅ Created LangChain Document from Docling output")
    print()
    print("Document Metadata:")
    for key, value in docling_document.metadata.items():
        print(f"  {key}: {value}")

    print(f"Content length: {len(docling_document.page_content):,} characters")

    #============================================
    # Recursive Chunking Method
    #============================================
    # split_documents_into_chunks()
    # Ensure documents is a list (required for iteration)
    documents = [docling_document] if not isinstance(docling_document, list) else docling_document



    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2500,  # the maximum number of characters in a chunk: we selected this value arbitrarily
        chunk_overlap=100,  # the number of characters to overlap between chunks
        add_start_index=True,  # If `True`, includes chunk's start index in metadata
        strip_whitespace=True,  # If `True`, strips whitespace from the start and end of every document
    )

    docs_processed = []
    for doc in documents:
        docs_processed += text_splitter.split_documents([doc])

    print(f"✅ Split {len(documents)} document(s) into {len(docs_processed)} chunks")

    #============================================
    # SECTION 1.4: The Embedding Model
    # ============================================
    embedding_model = load_embedding_model()

    # ============================================
    # SECTION 1.4: Vector Store
    # ============================================

    retriever = get_retriever(docs_processed, embedding_model, top_k=5, collection_name="instruction_tuning_chunks")

    # Use invoke with 'input' parameter for newer LangChain versions
    similar_chunks = retriever.invoke("What is instruction tuning?")
    # Alternatively, you can use: similar_chunks = retriever.get_relevant_documents("What is instruction tuning?")
    print(f"Retrieved {len(similar_chunks)} similar chunks:")
    for i, chunk in enumerate(similar_chunks):
        print(f"--------------------------------- chunk # {i+1} -------------------------------------")
        print(chunk.page_content[:1000])  # Print first 1000 characters of each chunk
        print(f"-----------------------------------------------------------------------------------\n")


    llm = init_chat_model(
        model=os.getenv("OPENAI_MODEL_ID"),
        api_key=os.getenv("OPENAI_API_KEY2"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model_provider="openai",
        temperature=0
    )
    prompt_template = ChatPromptTemplate.from_template(
        (
            "Please answer the following question based on the provided `context` that follows the question.\n"
            "If you do not know the answer then just say 'I do not know'\n"
            "question: {question}\n"
            "context: ```{context}```\n"
        )
    )

    chain = prompt_template | llm

    query = "What is instruction tuninig?"

    context = retrieve_context( query, retriever=retriever, remove_duplicates=True )

    context_text = ""
    for ch in context:
        context_text += ch.page_content

    #============================================
    # SECTION 1.6: Putting It All Together
    # Instruction tuning is a technique that enables pre-trained language models to learn from input-response pairs,
    # where the input is a natural language description of a task and the response is the desired output. This method has
    # been applied to both language-only and multimodal tasks. For language-only tasks, instruction tuning has improved
    # the zero-shot and few-shot performance of models like FLAN and InstructGPT. For multimodal tasks, it has been used
    # to generate synthetic instruction-following data for tasks such as image captioning and visual question answering.
    # In the context provided, it's mentioned that recent works like Alpaca, Vicuna, and WizardLM have adopted
    # instruction-tuning to train smaller language models using outputs generated from large foundation models from the
    # GPT family.
    #
    # ============================================

    # Document → Chunking → Embedding → Vector Store
    #                                            ↓
    # Query → Embedding → Similarity Search → Top-k Chunks → LLM → Answer


    response = chain.invoke({"context": context_text, "question": query})
    print('################################################################')
    print('#################### EXAMPLE 1 ##############################')

    print('Answer:')
    print(response.content)
    print('################################################################')
    print('################################################################')

    print('################################################################')
    print('##################### EXAMPLE 2 #############################')

    query = "How does Orca model compares to ChatGPT?"

    context = retrieve_context(
        query, retriever=retriever,
    )
    response = chain.invoke({"context": context, "question": query})
    print('Answer:')
    print(response.content)

    print('################################################################')
    print('##################### EXAMPLE 3 ##########################')

    query = "What is the diameter of the sun?"

    context = retrieve_context(
        query, retriever=retriever,
    )

    response = chain.invoke({"context": context, "question": query})
    print('Answer:')
    print(response.content)

    print('################################################################')
    print('################################################################')

    print('Simple RAG example complete.')