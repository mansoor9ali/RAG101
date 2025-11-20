import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich import print

from EnsembleRetriever import get_ensemble_retriever
from embeddingsUtiles import load_embedding_model
from utiles import get_retriever, load_pdf_docling, retrieve_context

load_dotenv()

if __name__ == '__main__':
    print('Starting Reranking RAG example...')
    if not os.path.exists("./data"):
        os.mkdir("./data")

    documents = load_pdf_docling("./data/8a9ebed0-815a-469a-87eb-1767d21d8cec.pdf")

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        # separators=["\n\n\n", "\n\n"],
        chunk_size=1024,
        chunk_overlap=0,
        model_name="gpt-4",
        add_start_index=True,  # If `True`, includes chunk's start index in metadata
        strip_whitespace=True,  # If `True`, strips whitespace from the start and end of every document
    )

    docs = text_splitter.split_documents(documents)

    print(f"Split into {len(docs)} chunks of text")

    #============================================
    # The Embedding Model
    # ============================================
    embedding_model = load_embedding_model()


    #============================================
    # Hybrid Retriever
    # ============================================

    print('Now create Hybrid Retriever ....')
    hybrid_retriever = get_ensemble_retriever(docs, embedding_model, collection_name="hybrid_search", top_k=5)



    #============================================
    # Retrieve Context
    # ============================================
    print('Now Retrieve Context ....')
    query = "What are the specific factors contributing to Airbnb's increased operational expenses in the last fiscal year?"
    similar_chunks = retrieve_context(
        query, retriever=hybrid_retriever,
    )

    for i, chunks in enumerate(similar_chunks):
        print(f"--------------------------------- chunk # {i} -------------------------------------")
        print(chunks.page_content[:500])

    prompt_template = """
    You are a helpful assistant. Provide answers to users questions based on the provided context.

    Context:
    {context}

    Question:
    {question}


    """
    prompt = ChatPromptTemplate.from_template(prompt_template)

    llm = init_chat_model(
        model="deepseek-reasoner",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        model_provider="openai",
        temperature=0
    )

    chain = {"question": RunnablePassthrough(), "context": hybrid_retriever} | prompt | llm  | StrOutputParser()

    result = chain.invoke(query)

    # display(HTML(result))
    print(result)