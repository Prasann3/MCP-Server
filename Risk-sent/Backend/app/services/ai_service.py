import asyncio
from typing import Any, List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.logging import logging
from app.utils.uploads import extract_text_from_pdf
from app.db.client import mongo_client
from bson import ObjectId
from fastapi import UploadFile

## Setting up logger
logger = logging.getLogger(__name__)

class RiskSentAIService:
    def __init__(self):
        # 1. Initialize Embeddings (384 dimensions for all-MiniLM-L6-v2)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # 2. Splitters
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        self.db = None
        if mongo_client.db is not None :
            self.db = mongo_client.db
    
    async def connect_to_db(self) :
          try : 
           await mongo_client.connect()
           self.db = mongo_client.db
          except Exception as e :
            logger.error(f"Error occured in rag service {str(e)}")


    async def ingest_pdf(self, file_path: str, user_id: str, doc_id: str):
        logger.info(f"Starting ingestion for doc: {doc_id}")

        loop = asyncio.get_running_loop()

        # MOVE PDF extraction OFF the event loop
        text = await loop.run_in_executor(
            None,
            extract_text_from_pdf,
            file_path
        )

        logger.info(f"Extracted text from the file doc_id={doc_id}")

        if self.db is None:
            await self.connect_to_db()

        initial_doc = Document(page_content=text, metadata={"source": doc_id})
        parent_docs = self.parent_splitter.split_documents([initial_doc])

        number_of_parent_chunks = len(parent_docs)
        number_of_chunk_processed = 0

        for p_doc in parent_docs:
            percent_complete = number_of_chunk_processed / number_of_parent_chunks

            await mongo_client.db.document.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": {"percent_complete": int(percent_complete * 100)}}
            )

            parent_record = {
                "doc_id": doc_id,
                "owner_id": user_id,
                "text": p_doc.page_content,
                "metadata": p_doc.metadata
            }

            parent_insert = await mongo_client.db.parents.insert_one(parent_record)

            child_docs = self.child_splitter.split_text(p_doc.page_content)

            if child_docs:
                # 🔥 MOVE EMBEDDINGS OFF event loop too
                embeddings = await loop.run_in_executor(
                    None,
                    self.embeddings.embed_documents,
                    child_docs
                )

                child_records = [
                    {
                        "parent_id": parent_insert.inserted_id,
                        "doc_id": doc_id,
                        "owner_id": user_id,
                        "embedding": vector,
                        "text_snippet": c_text
                    }
                    for c_text, vector in zip(child_docs, embeddings)
                ]

                if child_records:
                    await mongo_client.db.children.insert_many(child_records)

            number_of_chunk_processed += 1

        await mongo_client.db.document.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": "processed" , "percent_complete" : 100}}
        )

        logger.info(f"Ingestion complete for {doc_id}")

    async def search_risks(self, query: str, doc_id: str):
            """Finds 'Parent' context by searching 'Child' vectors with doc filters."""
            try :
                if self.db is None :
                 await self.connect_to_db()
                query_vector = self.embeddings.embed_query(query)
                logger.info(f"Search result: {len(query_vector)}")
                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": "vector_index", 
                            "path": "embedding",
                            "queryVector": query_vector,
                            "numCandidates": 100,
                            "limit": 5,
                            "filter": {
                                "$and": [
                                    {"doc_id": doc_id}
                                ]
                            }
                        }
                    },
                    {
                        # Join with Parents to get the full context
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
                print(f"DEBUG: Found {len(results)} child chunks.")
                return results
                
            except Exception as e:
                logger.error(f"Error during document retrieval: {str(e)}")
                return []

    async def debug_search(self , query , user_id, doc_id):
        # STAGE 1: Check if Vector Search even finds the children
        query_vector = self.embeddings.embed_query(query)
        pipeline = [
                    {
                        "$vectorSearch": {
                            "index": "vector_index", 
                            "path": "embedding",
                            "queryVector": query_vector,
                            "numCandidates": 100,
                            "limit": 5,
                            "filter": {
                                "$and": [
                                    {"doc_id": doc_id}
                                ]
                            }
                        }
                    },
                    {
                        # Join with Parents to get the full context
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
        
        children = await mongo_client.db.children.aggregate(pipeline).to_list(length=5)
        print(f"DEBUG: Found {len(children)} child chunks.")
        if len(children) > 0:
            print(f"Sample Child parent_id: {children[0].get('parent_id')}")    

        return children            

rag_service = RiskSentAIService()