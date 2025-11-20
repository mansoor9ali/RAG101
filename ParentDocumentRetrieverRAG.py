import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich import print

from InMemoryStore import create_parent_retriever
from embeddingsUtiles import load_embedding_model
from utiles import load_pdf_docling, retrieve_context

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



    #============================================
    # The Embedding Model
    # ============================================
    embedding_model = load_embedding_model()

    # ============================================
    # Parent-Child Retriever , this creates two retrievers
    # ============================================
    parent_retriever, child_retriever = create_parent_retriever(documents, embedding_model, collection_name="parent_child_split-1")

    # Test the retriever
    query = "What are the specific factors contributing to Airbnb's increased operational expenses in the last fiscal year?"
    similar_chunks = retrieve_context(
        query, retriever=child_retriever,
    )
    for i, chunks in enumerate(similar_chunks):
        print(f"--------------------------------- chunk # {i} -------------------------------------")
        print(chunks.page_content)

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

    chain = {"question": RunnablePassthrough(), "context": parent_retriever} | prompt | llm | StrOutputParser()

    result = chain.invoke(query)

    # display(HTML(result))
    print(result)

