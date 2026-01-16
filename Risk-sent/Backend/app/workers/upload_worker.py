import asyncio
import struct
import json
import signal
from app.services.redis import redis_client
from app.core.logging import logging
from app.db.client import mongo_client
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bson import ObjectId

logger = logging.getLogger(__name__)

class UploadWorker:
    def __init__(self , queue_name):
        self.queue_name = queue_name
        self.running = True
        self.db = None
        self.MAX_JOB = 6

    async def start(self):
        # 1. Connect to Redis
        try :
            self.redis = redis_client
            # 2. Connect to Database
            await mongo_client.connect()
            self.db = mongo_client.db

            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)

            await self._redis_worker_loop()
        except Exception as e : 
            logger.error("Error occured during starting the worker... " , str(e))    


    async def _redis_worker_loop(self):
        """Pulls jobs from Redis and hands them to C++."""
    
        logger.info(f"Worker started. Listening to {self.queue_name}")
        try:
            while self.running:
                # Long-poll Redis
                while(self.MAX_JOB == 0) :
                    await asyncio.sleep(2)
                result = await self.redis.brpop(self.queue_name, timeout=2)
                if result:
                    _, message = result
                    job_data = json.loads(message)
                    # Create a task so we can handle multiple jobs concurrently
                    asyncio.create_task(self._process_job(job_data))
                    
        except Exception as e:
            logger.error(f"Redis Loop Error: {e}")


    async def _process_job(self, payload):
        """Orchestrates a single job."""
       
        self.MAX_JOB -= 1
        job_id = payload['job_id']
        data = payload['data']
        doc_id = data['doc_id']
        user_id = data['user_id']
        parent_docs_batch = data['parent_docs']

        logger.info(f"Processing batch for Job={job_id}, Doc={doc_id}")

        for p_data in parent_docs_batch:
            # 1. Insert Parent into DB
            parent_record = {
                "doc_id": doc_id,
                "owner_id": user_id,
                "text": p_data['text'],
                "metadata": p_data['metadata']
            }
            parent_insert = await self.db.parents.insert_one(parent_record)

            # 2. Split into Child Chunks
            child_texts = self.child_splitter.split_text(p_data['text'])
            
            if child_texts:
                # 3. Generate Embeddings (this is usually the bottleneck)
                # Ensure this is thread-safe if using local models
                embeddings = self.embeddings.embed_documents(child_texts)

                # 4. Bulk Insert Children
                child_records = [
                    {
                        "parent_id": parent_insert.inserted_id,
                        "doc_id": doc_id,
                        "owner_id": user_id,
                        "embedding": vector,
                        "text_snippet": text
                    }
                    for text, vector in zip(child_texts, embeddings)
                ]
                await self.db.children.insert_many(child_records)
                await self.db.document.update_one(
                    {"_id": ObjectId(doc_id)},
                    [
                        {
                            "$set": {
                                "number_of_chunk_processed": {
                                    "$add": ["$number_of_chunk_processed", 1]
                                }
                            }
                        },
                        {
                            "$set": {
                                "percent_complete": {
                                    "$toInt": {
                                        "$multiply": [
                                            {
                                                "$divide": [
                                                    "$number_of_chunk_processed",
                                                    "$number_of_parent_chunks"
                                                ]
                                            },
                                            100
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                )

        # 5. Update Progress in MongoDB
        # You may want to use $inc to increment 'number_of_chunk_processed' 
        # based on len(parent_docs_batch)
        await self.db.document.update_one(
            {"_id": ObjectId(doc_id)},
            [
                {
                    "$set": {
                        "status": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$number_of_chunk_processed",
                                        "$number_of_parent_chunks"
                                    ]
                                },
                                "processed",
                                "$status"
                            ]
                        },
                        "percent_complete": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$number_of_chunk_processed",
                                        "$number_of_parent_chunks"
                                    ]
                                },
                                100,
                                "$percent_complete"
                            ]
                        }
                    }
                }
            ]
        )
        self.MAX_JOB += 1


        
        

    def stop(self):
        """Cleanup logic."""
        self.running = False
        logger.info("Closing Event loop...")




async def main():
    worker = UploadWorker("upload_queue")

    try:
        await worker.start()
    except asyncio.CancelledError:
        pass
    finally:
        worker.stop()

# --- Main Entry Point ---
if __name__ == "__main__":
    asyncio.run(main())