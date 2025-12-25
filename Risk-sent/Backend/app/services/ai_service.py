import os
import pickle
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import InMemoryStore
from app.core.logging import logger

# Paths for persistence
INDEX_PATH = "risk_faiss_index"
DOCSTORE_PATH = "risk_parent_docs.pkl"

class RiskSentAIService:
    def __init__(self):
        # 1. Initialize Embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # 2. Splitters
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500)
        
        # 3. Persistence Logic: Try to load existing data
        if os.path.exists(INDEX_PATH) and os.path.exists(DOCSTORE_PATH):
           
            self.vectorstore = FAISS.load_local(
                INDEX_PATH, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            with open(DOCSTORE_PATH, "rb") as f:
                self.store = pickle.load(f)
        else:
          
            # Create a dummy start point for FAISS
            self.vectorstore = FAISS.from_texts(["Initializing..."], self.embeddings)
            self.store = InMemoryStore()

        # 4. The Retriever connects them
        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.store,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter,
        )

    def ingest_pdf(self, file_path: str):
        """Processes a PDF, adds to memory, and SAVES to disk."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
            
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        # Add to retriever
        self.retriever.add_documents(docs)
        
        # --- PERSISTENCE STEP ---
        # Save the vectorstore (Child chunks)
        self.vectorstore.save_local(INDEX_PATH)
        # Save the docstore (Parent chunks)
        with open(DOCSTORE_PATH, "wb") as f:
            pickle.dump(self.store, f)
            
        return f"Successfully indexed {len(docs)} pages and saved to local disk."

    def search_risks(self, query: str):
        """Finds the most relevant 'Parent' context."""
        logger.info("Looking into vector store")
        return self.retriever.invoke(query)

# Global instance
ai_service = RiskSentAIService()
logger.info("RAG services loaded successfully")