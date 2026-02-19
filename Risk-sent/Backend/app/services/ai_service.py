import asyncio
from typing import List
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
import sys
from app.utils.uploads import extract_text_from_pdf
from app.db.client import mongo_client
from bson import ObjectId

logging.basicConfig(
    level=logging.INFO, 
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiskSentAIService:
    def __init__(self):
        # 1. Initialize FastEmbed (ONNX-based, no Torch required)
        # BAAI/bge-small-en-v1.5 is fast, accurate, and 384-dimensional
        self.embeddings = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            threads=4 # Optimized for CPU usage in Docker
        )
        
        # 2. Splitters
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        self.db = None
        
        # Immediate check for db (though client handles connections)
        if hasattr(mongo_client, 'db') and mongo_client.db is not None:
            self.db = mongo_client.db
    
    async def connect_to_db(self):
        try:
            await mongo_client.connect()
            self.db = mongo_client.db
        except Exception as e:
            logger.error(f"Error occurred in RAG service connection: {str(e)}")

    async def ingest_pdf(self, file_path: str, user_id: str, doc_id: str):
        logger.info(f"Starting ingestion for doc: {doc_id}")
        loop = asyncio.get_running_loop()

        # PDF extraction remains in executor to avoid blocking the loop
        text = await loop.run_in_executor(None, extract_text_from_pdf, file_path)
        logger.info(f"Extracted text from doc_id={doc_id}")

        if self.db is None:
            await self.connect_to_db()

        initial_doc = Document(page_content=text, metadata={"source": doc_id})
        parent_docs = self.parent_splitter.split_documents([initial_doc])

        total_chunks = len(parent_docs)
        
        for i, p_doc in enumerate(parent_docs):
            # Update progress
            percent_complete = int((i / total_chunks) * 100)
            await self.db.document.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {"percent_complete": percent_complete}}
            )

            # Insert Parent
            parent_record = {
                "doc_id": doc_id,
                "owner_id": user_id,
                "text": p_doc.page_content,
                "metadata": p_doc.metadata
            }
            parent_insert = await self.db.parents.insert_one(parent_record)

            # Generate and Insert Children
            child_texts = self.child_splitter.split_text(p_doc.page_content)

            if child_texts:
                # FastEmbed is generally fast enough to run directly, 
                # but we use embed_documents which returns a list of vectors
                embeddings = self.embeddings.embed_documents(child_texts)

                child_records = [
                    {
                        "parent_id": parent_insert.inserted_id,
                        "doc_id": doc_id,
                        "owner_id": user_id,
                        "embedding": list(vector), # Ensure it's a list for BSON
                        "text_snippet": c_text
                    }
                    for c_text, vector in zip(child_texts, embeddings)
                ]

                if child_records:
                    await self.db.children.insert_many(child_records)

        # Final Status Update
        await self.db.document.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": "processed", "percent_complete": 100}}
        )
        logger.info(f"Ingestion complete for {doc_id}")

    async def search_risks(self, query: str, doc_id: str):
        try:
            if self.db is None:
                await self.connect_to_db()
            
            # FastEmbed usage for single query
            # We use embed_query which returns a single list
            query_vector = self.embeddings.embed_query(query)
            
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index", 
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": 100,
                        "limit": 5,
                        "filter": {"doc_id": doc_id}
                    }
                },
                {
                    "$lookup": {
                        "from": "parents",
                        "localField": "parent_id",
                        "foreignField": "_id",
                        "as": "parent_context"
                    }
                },
                { "$unwind": "$parent_context" },
                {
                    "$project": {
                        "text": "$parent_context.text",
                        "page": "$parent_context.metadata.page",
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            cursor = self.db.children.aggregate(pipeline)
            results = await cursor.to_list(length=5)
            return results
                
        except Exception as e:
            logger.error(f"Error during document retrieval: {str(e)}")
            return []

rag_service = RiskSentAIService()