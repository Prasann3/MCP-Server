import asyncio
import json
import time
import os
import signal
import sys
from app.services.redis import redis_client
from app.core.logging import logging
from app.db.client import mongo_client
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bson import ObjectId
from pymongo import InsertOne, UpdateOne

## Setting up logger
my_pid = os.getpid()
logger = logging.getLogger(f"upload_worker_{my_pid}")

class UploadWorker:
    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.running = True
        self.db = None
        self.MAX_JOB = 8
        self.active_tasks = set() # Track background tasks

    def handle_exit_signal(self , signum, frame):
            """Triggered when Autoscaler calls proc.terminate()"""
            logger.info(f"Termination signal received ({signum}) . Finishing current job...")
            self.running = False
     

    async def start(self):
        # 1. Connect to Redis and DB

        try:
            signal.signal(signal.SIGTERM, self.handle_exit_signal)
            signal.signal(signal.SIGINT, self.handle_exit_signal)
            self.redis = redis_client
            await mongo_client.connect()
            self.db = mongo_client.db

            # 2. Initialize FastEmbed (ONNX) - Matches your RAG Service
            self.embedding_model = FastEmbedEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                threads=4
            )
            
            self.child_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400, 
                chunk_overlap=40
            )

            await self._redis_worker_loop()
        except Exception as e: 
            logger.error(f"Error occurred during starting the worker: {str(e)}")   

        finally:
            # CLEANUP PHASE: This runs after self.running is False
            if self.active_tasks:
                logger.info(f"Waiting for {len(self.active_tasks)} jobs to finish...")
                await asyncio.gather(*self.active_tasks) 
            logger.info("All jobs finished. Cleanup complete.")     

    async def _redis_worker_loop(self):
        """Pulls jobs from Redis and handles them concurrently."""
        logger.info(f"Worker started. Listening to {self.queue_name}")
        try:
            while self.running:
                while self.MAX_JOB <= 0:
                    await asyncio.sleep(2)
                    continue
                
                # Long-poll Redis
                result = await self.redis.brpop(self.queue_name, timeout=2)
                if result:
                    _, message = result
                    job_data = json.loads(message)

                    # Manage concurrency
                    self.MAX_JOB -= 1
                    task = asyncio.create_task(self._process_job(job_data))
                    self.active_tasks.add(task)
                    task.add_done_callback(self.active_tasks.discard)

            logger.info("Loop stopped. No longer taking new jobs.")       
                    
        except Exception as e:
            logger.error(f"Redis Loop Error: {e}")

    async def _process_job(self, payload):
        """Orchestrates a single job batch."""
        job_id = payload['job_id']
        data = payload['data']
        doc_id = data['doc_id']
        user_id = data['user_id']
        parent_docs_batch = data['parent_docs']
        
        start_time = time.perf_counter()
        logger.info(f"Processing batch for Job={job_id}, Doc={doc_id}")

        parent_operations = []
        child_operations = []
        document_operations = []

        try:
            for p_data in parent_docs_batch:
                parent_id = ObjectId()

                parent_record = {
                    "_id": parent_id,
                    "doc_id": doc_id,
                    "owner_id": user_id,
                    "text": p_data['text'],
                    "metadata": p_data['metadata']               
                }
                parent_operations.append(InsertOne(parent_record))
                
                child_texts = self.child_splitter.split_text(p_data['text'])
                
                if child_texts:
                    # 3. Generate Embeddings using FastEmbed
                    # Returns a list of vectors
                    embeddings = self.embedding_model.embed_documents(child_texts)

                    # 4. Create Child Records
                    for text, vector in zip(child_texts, embeddings):
                        child_operations.append(InsertOne({
                            "parent_id": parent_id,
                            "doc_id": doc_id,
                            "owner_id": user_id,
                            "embedding": list(vector), # Convert numpy array to list for BSON
                            "text_snippet": text
                        }))

                    # 5. Track progress in the main document
                    document_operations.append(UpdateOne(
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
                    ))

            # Bulk Write Operations
            if child_operations:
                await self.db.children.bulk_write(child_operations)
            if parent_operations:
                await self.db.parents.bulk_write(parent_operations)

            # Check if document is fully processed
            document_operations.append(UpdateOne(
                {"_id": ObjectId(doc_id)},
                [
                    {
                        "$set": {
                            "status": {
                                "$cond": [
                                    {"$gte": ["$number_of_chunk_processed", "$number_of_parent_chunks"]},
                                    "processed",
                                    "$status"
                                ]
                            },
                            "percent_complete": {
                                "$cond": [
                                    {"$gte": ["$number_of_chunk_processed", "$number_of_parent_chunks"]},
                                    100,
                                    "$percent_complete"
                                ]
                            }
                        }
                    }
                ]            
            ))

            if document_operations:
                await self.db.document.bulk_write(document_operations)
                
            duration = time.perf_counter() - start_time
            logger.info(f"Finished batch for Job={job_id} in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
        finally:
            self.MAX_JOB += 1

    def stop(self):
        self.running = False
        logger.info("Stopping Worker...")

async def main():
    worker = UploadWorker("upload_queue")
    try:
        await worker.start()
    except asyncio.CancelledError:
        pass
    finally:
        worker.stop()
        logger.info("Worker stopped")

if __name__ == "__main__":
    asyncio.run(main())