# Risk-Sent: High-Performance Financial Document Intelligence

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![C++](https://img.shields.io/badge/C++-17-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-05998b.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Redis](https://img.shields.io/badge/Redis-Task--Queue-red)

**Risk-Sent** is an advanced AI-powered intelligence platform designed for financial analysts to automate the extraction, analysis, and querying of complex financial filings (like 10-Ks). By bridging high-performance native C++ parsing with modern RAG architectures, it solves the bottlenecks of traditional document processing.

---

## 🏗️ System Architecture

Risk-Sent utilizes a distributed, multi-process architecture to ensure that CPU-intensive parsing never blocks the API event loop.

```mermaid
graph TD
    A[React Frontend] -->|POST /uploads| B[FastAPI Server]
    B -->|Push Job| C[(Redis Queue)]
    C -->|Pull Job| D[Python Parsing Worker]
    D <-->|4-Byte Header Stream Protocol| E[C++ Native Parser]
    D -->|Parent-Child Chunks| F[(Redis Upload Queue)]
    F -->|Pull Job| G[Python Upload Worker]
    G -->|Bulk Write| H[(MongoDB Atlas Vector Search)]
    B -->|Query| I[Agent Manager]
    I <--> J[MCP Server Tools]
    J -->|Semantic Search| H

    ⚡ The High-Performance C++ Bridge
To bypass the Python GIL and maximize throughput, Risk-Sent offloads PDF parsing to a multi-threaded C++ binary.

Stream Protocol: Python and C++ communicate via streams using a custom protocol where the first 4 bytes indicate the payload size. This ensures zero-loss, high-speed data transfer.

Efficiency: This allows the system to utilize 100% of available CPU cores for parsing while keeping the FastAPI event loop responsive.


✨ Core Features
1. Advanced Parent-Child RAG
Unlike basic RAG, Risk-Sent uses a Parent-Child text pattern:

Child Chunks: Small snippets optimized for high-precision vector embedding and retrieval.

Parent Chunks: The larger surrounding context retrieved once a match is found, ensuring the LLM understands the full financial narrative.

2. MCP (Model Context Protocol) Server
The system invokes an MCP server as a child process. This allows the LLM to dynamically call tools—such as semantic_search—to query the MongoDB vector database in real-time, functioning as a truly agentic system.

3. Intelligent Conversation Memory
A custom memory manager provides the LLM with both short-term and long-term conversation history. This ensures the agent maintains full context over long research sessions.

4. Scalable Redis Workers
Parsing Worker: Pulls from parse_queue, manages the C++ lifecycle, and generates chunks.

Upload Worker: Pulls from upload_queue and performs bulk writes to MongoDB to minimize database round-trips.


🛠️ Tech Stack
Server: FastAPI, Python 3.12

Language Bridge: C++ (Native Binary)

Database: MongoDB (NoSQL + Vector Store)

Orchestration: Redis (Job Queues), Docker

AI: LangChain, MCP, OpenAI/Anthropic LLMs

Frontend: React + Vite



📁 Project Structure

.
├── app/
│   ├── api/v1/routes/      # Chats, Uploads, and User management
│   ├── services/           # AI Service, Agent Manager, Redis logic
│   ├── workers/            # Multi-process Task Workers
│   │   ├── worker.cpp      # Source for high-efficiency C++ parser
│   │   ├── parsing_worker  # Orchestrates C++ child process
│   │   └── upload_worker   # Handles bulk database ingestion
│   └── main.py             # Entry point for FastAPI
├── mcp-server/             # Model Context Protocol tools & logic
├── Dockerfile              # Multi-process container configuration
└── requirements.txt        # Python dependencies


⚙️ Setup & Deployment
Build the Image
The Dockerfile is configured to compile the C++ source and set up the Python 3.12 environment automatically.

# docker build -t risk-sent-app .

Run the System
Ensure you have a .env file with your MONGO_URI and OPENAI_API_KEY

docker run -d \
  -p 8000:8000 \
  --name risk-sent-container \
  --restart unless-stopped \
  risk-sent-app


  Accessing the API
Once running, you can interact with the API via the Swagger UI at http://localhost:8000/docs.


👨‍💻 Target Audience
Risk-Sent is purpose-built for Financial Analysts and Risk Managers who need to extract insights from thousands of pages of text without the manual overhead of traditional document review.