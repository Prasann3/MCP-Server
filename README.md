# Risk-Sent: High-Performance Financial Document Intelligence

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![C++](https://img.shields.io/badge/C++-17-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-05998b.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Redis](https://img.shields.io/badge/Redis-Task--Queue-red)

**Risk-Sent** is a high-performance AI-powered financial document intelligence platform designed to automate the extraction, analysis, and querying of complex regulatory filings (e.g., 10-K, 10-Q, annual reports). By combining native C++ performance with modern Retrieval-Augmented Generation (RAG) architectures, Risk-Sent eliminates the traditional bottlenecks of large-scale document processing.

---

## 🚀 Overview

Financial analysts spend countless hours navigating massive filings to locate risk signals, disclosures, and narrative insights. Risk-Sent transforms this workflow by:

* ⚡ Parsing documents using a multi-threaded C++ engine
* 🧠 Structuring knowledge through Parent–Child RAG
* 🔎 Enabling semantic search over financial narratives
* 🤖 Providing agentic querying via MCP tools
* 📈 Maintaining long-running contextual conversations

The system is designed for **throughput, scalability, and low-latency querying** under heavy workloads.

---

## 🏗️ System Architecture

Risk-Sent uses a distributed, multi-process architecture where CPU-intensive workloads are isolated from the API layer to maintain responsiveness.

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
```

### ⚡ High-Performance C++ Bridge

To bypass Python's GIL and maximize throughput, Risk-Sent offloads PDF parsing to a multi-threaded C++ binary.

* **Stream Protocol:** Python and C++ communicate using a custom 4-byte header protocol that encodes payload size, ensuring reliable high-speed streaming.
* **Efficiency:** Full CPU utilization during parsing while the FastAPI event loop remains non-blocking.

---

## ✨ Core Features

### 1️⃣ Advanced Parent–Child RAG

Unlike traditional RAG pipelines:

* **Child Chunks:** Small semantic units optimized for embedding accuracy.
* **Parent Chunks:** Larger contextual segments retrieved after a match to preserve narrative coherence.

This architecture improves reasoning over long financial disclosures.

### 2️⃣ MCP (Model Context Protocol) Server

Risk-Sent invokes an MCP server as a child process, allowing the LLM to dynamically call tools such as `semantic_search` against MongoDB Atlas Vector Search. This enables true agentic behavior.

### 3️⃣ Intelligent Conversation Memory

A custom memory manager maintains:

* **Short-term memory:** Recent conversation context
* **Long-term memory:** Persistent research history

This allows analysts to conduct extended investigative sessions without context loss.

### 4️⃣ Scalable Redis Workers

* **Parsing Worker:** Consumes from `parse_queue`, manages C++ lifecycle, and generates document chunks.
* **Upload Worker:** Consumes from `upload_queue` and performs bulk MongoDB writes to minimize round trips.

---

## 🛠️ Tech Stack

| Layer           | Technology                    |
| --------------- | ----------------------------- |
| Backend API     | FastAPI, Python 3.12          |
| Native Engine   | C++17                         |
| Vector Database | MongoDB Atlas (Vector Search) |
| Queue System    | Redis                         |
| AI Framework    | LangChain, MCP                |
| LLM Providers   | OpenAI / Anthropic            |
| Frontend        | React + Vite                  |
| Deployment      | Docker                        |

---

## 📁 Project Structure

```
.
├── app/
│   ├── api/v1/routes/      # Chats, uploads, and user management
│   ├── services/           # AI services, agent manager, Redis logic
│   ├── workers/            # Multi-process task workers
│   │   ├── worker.cpp      # High-efficiency C++ parser
│   │   ├── parsing_worker  # Parsing orchestration
│   │   └── upload_worker   # Bulk database ingestion
│   └── main.py             # FastAPI entry point
├── mcp-server/             # MCP tools and logic
├── Dockerfile              # Multi-process container setup
└── requirements.txt        # Python dependencies
```

---

## ⚙️ Setup & Deployment

### 1️⃣ Build the Image

The Dockerfile compiles the C++ parser and prepares the Python 3.12 runtime automatically.

```bash
docker build -t risk-sent-app .
```

### 2️⃣ Configure Environment

Create a `.env` file:

```env
MONGO_URI=your_mongodb_uri
OPENAI_API_KEY=your_api_key
```

### 3️⃣ Run the System

```bash
docker run -d \
  -p 8000:8000 \
  --name risk-sent-container \
  --restart unless-stopped \
  risk-sent-app
```

---

## 📡 Accessing the API

Once running, access the interactive Swagger documentation:

👉 [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🎯 Target Audience

Risk-Sent is built for:

* Financial Analysts
* Risk Managers
* Research Analysts
* Compliance Teams

who need to extract actionable insights from thousands of pages of financial disclosures with minimal manual effort.


