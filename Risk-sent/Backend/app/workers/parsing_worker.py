import asyncio
import signal
import struct
import json
import time
import sys
from uuid import uuid4
import os
import subprocess
from app.services.redis import redis_client
from app.core.logging import logging
from app.db.client import mongo_client
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bson import ObjectId
from app.core.config import settings     

my_pid = os.getpid()
logger = logging.getLogger(f"parsing_worker_{my_pid}")

class ParseWorker:
    def __init__(self, cpp_executable , queue_name):
        self.cpp_executable = cpp_executable
        self.queue_name = queue_name
        self.process = None
        self.futures = {}
        self.running = True
        self.db = None
        self.MAX_JOB = 4
        self.current_jobs = 0
        self.active_tasks = set() # Track background tasks

    def handle_exit_signal(self, signum, frame):
        """Triggered when Autoscaler calls proc.terminate()"""
        logger.info(f"Termination signal received ({signum}). Finishing current job...")
        self.running = False                      

    async def start(self):
        # 1. Connect to Redis
        signal.signal(signal.SIGTERM, self.handle_exit_signal)
        signal.signal(signal.SIGINT, self.handle_exit_signal)
        try :
            self.redis = redis_client

            # 2. Connect to Database
            await mongo_client.connect()
            self.db = mongo_client.db
            # 3. Launch C++ Child Process
            if settings.ENV == "PROD" :
                self.process = await asyncio.create_subprocess_exec(
                    self.cpp_executable,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=None ,
                    start_new_session=True
                )
            else :
                  self.process = await asyncio.create_subprocess_exec(
                    "wsl",  
                    self.cpp_executable,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=None ,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )  
            logger.info("Created the cpp child process successfully")

            # 2. Splitters
            self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

            # 4. Start background loops
            # One to read from C++, one to pull from Redis
            self.reader_task = asyncio.create_task(self._cpp_reader_loop())
            await self._redis_worker_loop()
        except Exception as e : 
            logger.error("Error occured during starting the worker... " , str(e))    

        finally : 
            await self.stop()    

    async def _cpp_reader_loop(self):
        """Listens to C++ stdout and dispatches results."""
        try:
            while self.running or self.current_jobs > 0:
                # Read 4-byte header
                header = await self.process.stdout.readexactly(4)
                msg_len = struct.unpack('I', header)[0]
                
                # Read JSON payload
                raw_data = await self.process.stdout.readexactly(msg_len)
                data = json.loads(raw_data.decode('utf-8'))
                
                # Wake up the specific awaiting Redis task
                job_id = data.get("job_id")
                if job_id in self.futures:
                    self.futures.pop(job_id).set_result(data)
        except asyncio.IncompleteReadError:
            logger.info("C++ process pipe closed.") 
            for job_id, future in self.futures.items():
                if not future.done():
                    future.set_exception(RuntimeError("C++ process terminated prematurely"))
            self.futures.clear()                  
        except Exception as e:
            logger.error("Error occured while reading from stdout stream " , str(e))


    async def _redis_worker_loop(self):
        """Pulls jobs from Redis and hands them to C++."""
    
        logger.info(f"Worker started. Listening to {self.queue_name}")
        try:
            while self.running:
                # Long-poll Redis
                result = await self.redis.brpop(self.queue_name, timeout=2)
                if result:
                    _, message = result
                    job_data = json.loads(message)
                    # Create a task so we can handle multiple jobs concurrently
                    self.current_jobs += 1
                    task =  asyncio.create_task(self._process_job(job_data))
                    self.active_tasks.add(task)
                    task.add_done_callback(self.active_tasks.discard)
                    while self.current_jobs >= self.MAX_JOB :
                        await asyncio.sleep(2)
      
        except Exception as e:
            print(f"Redis Loop Error: {e}")

    async def send_job_to_cpp(self , job_data) :
        """Sends the job to cpp child process"""

        payload = json.dumps(job_data).encode("utf-8")
        length = len(payload)

        # Pack length as 4 bytes 
        header = struct.pack("I", length)

        try :
            self.process.stdin.write(header)
            self.process.stdin.write(payload)
            await self.process.stdin.drain()
        except Exception as e : 
            logger.error(f"Error occured while sending the job with id={job_data["job_data"]} to child process " , str(e))    

    async def _process_job(self, job_data):
        """Orchestrates a single job."""
        job_id = job_data['job_id']
        # Create a "pager" for this specific job
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[job_id] = future
        start_time = time.perf_counter()
        # Send to C++ via stdin
        logger.info(f"Sending the job id={job_id} to child process for parsing")
        await self.send_job_to_cpp({ "job_id" : job_data['job_id'] , "file_path" : job_data['file_path']})

        # Wait for C++ to respond via the reader_loop
        result = await future
        logger.info(f"Job={job_id} Text parsing completed. Text length: {len(result['text'])}")

        if (result["status"] == "Failed") :
            await self.db.document.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": "Failed" , "percent_complete" : 100 , "error_message" : result["error"]}}
            )
            return

        text = result['text']
        doc_id = job_data['doc_id']
        user_id = job_data['user_id']


        initial_doc = Document(page_content=text, metadata={"source": doc_id})
        parent_docs = self.parent_splitter.split_documents([initial_doc])

        number_of_parent_chunks = len(parent_docs)
        number_of_chunk_processed = 0
        logger.info(f"doc_id={doc_id} The document has been splited to {number_of_parent_chunks} chunks")

        await self.db.document.update_one(
            {"_id" : ObjectId(doc_id)} ,
            {"$set" : {
                "number_of_chunk_processed" : number_of_chunk_processed ,
                "number_of_parent_chunks" : number_of_parent_chunks ,
                "percent_complete" : 0
            }}
        )

        batch_size = 10
        # Iterate through parent_docs in steps of 10
        for i in range(0, number_of_parent_chunks, batch_size):
            # Slice the list to get a batch
            batch_slice = parent_docs[i : i + batch_size]
            # Prepare the list of parent doc content/metadata
            parent_list = [
                {"text": p.page_content, "metadata": p.metadata} 
                for p in batch_slice
            ]

            # Construct the job object
            queue_job = {
                "job_id": str(uuid4()),
                "data": {
                    "doc_id": doc_id,
                    "user_id": user_id,
                    "parent_docs": parent_list
                }
            }

            # Push to Redis queue "upload_queue"
            # Using rpush to add to the end of the list
            duration = time.perf_counter() - start_time
            await self.redis.rpush("upload_queue", json.dumps(queue_job))
            if settings.ENV == "DEV" :
             file_path = f"C:/Users/Lenovo/OneDrive/Desktop/DE Shaw/Risk-sent/Backend/app/uploads/pdfs/{job_data['filename']}.pdf"
            else : 
                file_path = f"{settings.WORKING_DIR}/app/uploads/pdfs/{job_data['filename']}.pdf"
            if os.path.exists(file_path) :
                os.remove(file_path)
                logger.info(f"File {file_path} has been deleted after processing.")

            self.current_jobs -= 1
            logger.info(f"Batched {len(batch_slice)} docs for doc_id {doc_id} to upload_queue in Time: {duration:.2f}s")
                

    async def stop(self):
        """Cleanup logic."""
        self.running = False
        
        # Give active tasks a moment to finish via the loop
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to finish...")
            await asyncio.wait(list(self.active_tasks), timeout=20)

        if self.process:
            logger.info("Closing C++ stdin and terminating process...")
            try:
                self.process.stdin.close()
                await self.process.stdin.wait_closed()
                self.process.terminate()
                await self.process.wait()
            except:
                pass
        
            self.reader_task.cancel()

async def main():
    worker = ParseWorker(f"{settings.WORKING_DIR}/app/workers/worker", "parse_queue")

    try:
        await worker.start()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Worker stopped")

# --- Main Entry Point ---
if __name__ == "__main__":
    asyncio.run(main())
