"""
UI components module containing all Streamlit UI rendering logic
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Tuple, List, Any
import logging

from langchain_core.documents import Document

from document_processor import DocumentProcessor
from Agentic_RAG.services.vector_store import VectorStoreService

from Agentic_RAG.config.settings import AVAILABLE_EMBEDDING_MODELS

logger = logging.getLogger(__name__)

class UIComponents:
    """UI components class that encapsulates all Streamlit UI rendering logic"""
    
    # 1. Render model selection components
    @staticmethod
    def render_model_selection(available_models: List[str], current_model: str, embedding_models: List[str], current_embedding_model: str) -> Tuple[str, str]:
        """
        available_models - List of available models
        current_model - Currently selected model
        embedding_models - List of available embedding models
        current_embedding_model - Currently selected embedding model

        @return (user selected model, user selected embedding model)
        """
        st.sidebar.header("⚙️ Settings")
        
        new_model = st.sidebar.selectbox(
            "Choose model",
            options=available_models,
            index=available_models.index(current_model) if current_model in available_models else 0,
            help="Select the language model to use"
        )
        
        new_embedding_model = st.sidebar.selectbox(
            "Embedding model",
            options=embedding_models,
            index=embedding_models.index(current_embedding_model) if current_embedding_model in embedding_models else 0,
            help="Select the model used for document embeddings"
        )
        
        return new_model, new_embedding_model
    

    # 2. Render RAG settings components
    @staticmethod
    def render_rag_settings(rag_enabled: bool, similarity_threshold: float, default_threshold: float) -> Tuple[bool, float]:
        """
        rag_enabled - Whether to enable RAG
        similarity_threshold - Similarity threshold
        default_threshold - Default similarity threshold

        @return (whether RAG is enabled, similarity threshold)
        """
        st.sidebar.subheader("RAG Settings")
        
        new_rag_enabled = st.sidebar.checkbox(
            "Enable RAG",
            value=rag_enabled,
            help="Enable Retrieval-Augmented Generation using uploaded documents to enhance answers"
        )
        
        new_similarity_threshold = st.sidebar.slider(
            "Similarity threshold",
            min_value=0.0,
            max_value=1.0,
            value=similarity_threshold,
            step=0.05,
            help="Adjust the retrieval similarity threshold; higher values require more precise matches"
        )
        
        # Change the reset similarity threshold button to use container width
        if st.sidebar.button("Reset similarity threshold", use_container_width=True):
            new_similarity_threshold = default_threshold
            
        return new_rag_enabled, new_similarity_threshold
    

    # 3. Render chat statistics
    @staticmethod
    def render_chat_stats(chat_history):
        """
        chat_history - Chat history manager
        """
        st.sidebar.header("💬 Conversation History")
        stats = chat_history.get_stats()
        st.sidebar.info(f"Total messages: {stats['total_messages']} User messages: {stats['user_messages']}")
        
        if st.sidebar.button("📥 Export conversation history", use_container_width=True):
            csv = chat_history.export_to_csv()
            if csv:
                st.sidebar.download_button(
                    label="Download CSV file",
                    data=csv,
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        if st.sidebar.button("✨ Clear conversation", use_container_width=True):
            chat_history.clear_history()
            st.rerun()


    # 4. Render document upload components
    @staticmethod
    def render_document_upload(
        document_processor: DocumentProcessor,
        vector_store: VectorStoreService,
        processed_documents: List[str]
    ) -> Tuple[List[Document], VectorStoreService]:
        """
        document_processor - Document processor
        vector_store - Vector store service
        processed_documents - List of processed documents

        @return (all_docs, vector_store)
        """
        with st.expander("📁 Upload RAG documents", expanded=not bool(processed_documents)):
            uploaded_files = st.file_uploader(
                "Upload PDF, TXT files", 
                type=["pdf", "txt"],
                accept_multiple_files=True
            )
            
            if not vector_store.vector_store:
                st.warning("⚠️ Please configure the vector store in the sidebar to enable document processing.")
            
            all_docs = []
            if uploaded_files:
                if st.button("Process documents"):
                    with st.spinner("Processing documents..."):
                        for uploaded_file in uploaded_files:
                            if uploaded_file.name not in processed_documents:
                                try:
                                    # Handle all file types uniformly
                                    result = document_processor.process_file(uploaded_file)
                                    
                                    if isinstance(result, list):
                                        # The result is a list of Documents (PDF)
                                        all_docs.extend(result)
                                    else:
                                        # The result is plain text content (TXT, DOCX, etc.)
                                        doc = Document(
                                            page_content=result, 
                                            metadata={"source": uploaded_file.name}
                                        )
                                        all_docs.append(doc)
                                    
                                    processed_documents.append(uploaded_file.name)
                                    st.success(f"✅ Processed: {uploaded_file.name}")
                                except Exception as e:
                                    st.error(f"❌ Failed to process: {uploaded_file.name} - {str(e)}")
                            else:
                                st.warning(f"⚠️ Already exists: {uploaded_file.name}")
                
                if all_docs:
                    with st.spinner("Building vector index..."):
                        vector_store.vector_store = vector_store.create_vector_store(all_docs)
            
            # Show the list of processed documents
            if processed_documents:
                st.subheader("Processed documents")
                for doc in processed_documents:
                    st.markdown(f"- {doc}")
                
                if st.button("Clear all documents"):
                    with st.spinner("Clearing vector index..."):
                        vector_store.clear_index()
                        processed_documents.clear()
                    st.success("✅ All documents cleared")
                    st.rerun()
            
            return all_docs, vector_store


    # 5. Render chat history
    @staticmethod
    def render_chat_history(chat_history):
        """
        chat_history - Chat history manager
        """
        for message in chat_history.history:
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == "assistant_think":
                with st.expander("💡 View reasoning process <think> ... </think>"):
                    st.markdown(content)
            elif role == "retrieved_doc":
                with st.expander(f"🔎 View retrieved document chunks", expanded=False):
                    if isinstance(content, list):
                        for idx, doc in enumerate(content, 1):
                            st.markdown(f"**Document chunk {idx}:**\n{doc}")
                    else:
                        st.markdown(content)
            else:
                with st.chat_message(role):
                    st.write(content) 