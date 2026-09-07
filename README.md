# 🛠️ Enterprise IT Support Agentic RAG Copilot

**An AI-powered IT support assistant that thinks before it answers.**

Instead of blindly retrieving documents and generating a response, this system reasons through *where* the best answer is likely to live — the company knowledge base, the open web, or a direct reply — and only escalates to the next source when the evidence it already has isn't good enough.

Built as a **Forward Deployed Engineer (FDE) style project**: not a notebook demo, but a deployable internal product with an API, a UI, an ingestion pipeline, audit logging, and a container-based deployment on **Render**.

---

## 1. The Problem

**NovaRetail**, a fictional 3,000-employee retail company, has an internal IT team maintaining a sprawling library of documents — VPN setup guides, password policies, MFA rules, software installation steps, laptop troubleshooting guides, and service-desk runbooks.

Despite this, employees keep filing repetitive support tickets. Why?

| Root Cause | Impact |
|---|---|
| Employees don't know which document has the answer | Tickets get filed for things already documented |
| Keyword search returns too much noise | Employees give up and ask a human instead |
| A plain chatbot may hallucinate | Wrong answers create security and compliance risk |
| Internal docs can be incomplete or stale | Some questions simply can't be answered from the KB |
| Some questions need live, external information | E.g. "Is Teams down right now?" — no internal doc has that |

**Example — this is genuinely two different problems wearing the same "chatbot" costume:**

> *"How do I connect to the company VPN from home?"*
> → The answer lives entirely in the private KB. The system should answer **from company data only** and never touch the public internet.

> *"What is the latest Microsoft Teams outage guidance?"*
> → The internal KB has nothing current on this. The system needs to **recognize its own knowledge gap**, fall back to a live web search, and clearly flag the answer as externally sourced.

A single, fixed pipeline can't handle both cases well. That's the actual engineering problem.

### Business Goal

Build a secure IT Support Copilot that:

1. Always searches trusted private knowledge **first**.
2. Grades whether the retrieved evidence is actually good enough to answer with.
3. Falls back to web search **only** when private knowledge is insufficient.
4. Rewrites weak/vague queries and retries, with a retry guard to avoid infinite loops.
5. Generates answers that are grounded in retrieved evidence — not hallucinated.
6. Exposes its **decision path** for transparency, trust, and debugging.
7. Lets authorized staff add new company documents without touching code.

---

## 2. Why This Is an FDE Problem, Not a Notebook Problem

A Forward Deployed Engineer doesn't stop at "the model works in a notebook." The job is to take a customer's messy, real-world problem and turn it into something a non-technical employee can actually use — reliably, securely, and observably.

```
Customer Problem
      ↓
Discovery & Requirements
      ↓
Solution Architecture
      ↓
Data / Knowledge Integration
      ↓
Agentic RAG Development
      ↓
API Development
      ↓
User Interface
      ↓
Security + Audit + Testing
      ↓
Deployment
      ↓
Observe + Improve
```

This repository is structured to demonstrate every layer of that chain — not just the RAG logic in the middle.

---

## 3. The Solution: Agentic RAG, Not Static RAG

A standard RAG pipeline looks like this:

```
Question → Retrieve → Generate
```

It has no judgment. It retrieves once, generates once, and hopes for the best — even if the retrieved chunks are irrelevant.

This system instead behaves like a careful support engineer would: check the obvious source first, judge whether what you found is actually useful, and only escalate when you have to.

```
Question
 → Route (is this even an IT question, or just small talk?)
 → Retrieve from private KB
 → Grade the evidence: good enough, or weak?
 → If weak → search the web
 → Grade that evidence too
 → If still weak → rewrite the query and retry (bounded)
 → Generate a grounded, source-aware answer
```

### High-Level Architecture

```
                   ┌─────────────────────┐
                   │   Employee / User    │
                   └──────────┬───────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ HTML / CSS / JS Web  │
                   │        UI            │
                   └──────────┬───────────┘
                              │ POST /api/chat
                              ▼
                   ┌─────────────────────┐
                   │       FastAPI        │
                   └──────────┬───────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │      LangGraph       │
                   │ Agentic RAG Control  │
                   └──────────┬───────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
       ┌───────────────┐              ┌──────────────┐
       │  Private KB    │              │ Tavily Web    │
       │  (Pinecone)    │              │ Search        │
       └───────┬────────┘              └──────┬────────┘
               │                             │
               └──────────────┬──────────────┘
                              ▼
                     ┌────────────────┐
                     │   Groq / OpenAI │
                     │  Grounded Answer│
                     └────────────────┘
```

### The Full Decision Graph

```
Question
   ↓
[1] Route Question
   ├── Greeting / small talk ──────────────→ Direct Answer
   │
   └── IT support question
                ↓
[2] Retrieve from Private Pinecone KB
                ↓
[3] Grade Private Evidence
       ┌────────┴────────┐
       │                 │
     GOOD               WEAK
       │                 │
       ▼                 ▼
Generate from KB    [4] Tavily Web Search
                         ↓
                  [5] Grade Web Evidence
                    ┌────┴─────┐
                    │          │
                  GOOD        WEAK
                    │          │
                    ▼          ▼
              Generate Web  [6] Rewrite Query
                               ↓
                         Retry Private KB
                               ↓
                        Max retries reached?
                               ↓
                    Insufficient Evidence
                    (transparent fallback)
```

**Why this matters:** the "grade the evidence" step is the whole point. Most RAG demos skip it and just concatenate whatever the vector search returns into the prompt. Here, every retrieval is checked for relevance *before* it's allowed to influence the answer — which is what actually prevents hallucination and silent wrong answers in a support context where being confidently wrong has real cost.

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent workflow | **LangGraph** | Stateful routing and conditional decision-making |
| LLM | **Groq** (with OpenAI fallback) | Routing, grading, query rewriting, answer generation |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | Local, free, 384-dimensional embeddings |
| Vector DB | **Pinecone** | Private enterprise knowledge base |
| External search | **Tavily** | Fallback for current / external information |
| API | **FastAPI** | Backend and REST endpoints |
| Frontend | HTML / CSS / JavaScript | Employee-facing chat interface |
| Audit | SQLite | Decision-path logging for every query |
| Packaging | **Docker** | Reproducible, portable deployment |
| Hosting | **Render** | Managed container deployment |

---

## 5. Project Structure

```
FDE_Agentic_RAG_IT_Copilot/
│
├── app/
│   ├── api/
│   │   └── routes.py              # Chat, health, and ingestion endpoints
│   │
│   ├── core/
│   │   ├── config.py              # Environment configuration
│   │   └── logging.py             # Logging configuration
│   │
│   ├── rag/
│   │   ├── state.py               # LangGraph state + structured decisions
│   │   ├── vectorstore.py         # Pinecone + embeddings
│   │   └── workflow.py            # Complete Agentic RAG graph
│   │
│   ├── services/
│   │   ├── audit.py               # SQLite query audit
│   │   └── ingestion.py           # PDF / TXT / MD / DOCX loading + chunking
│   │
│   └── main.py                    # FastAPI application entrypoint
│
├── data/
│   └── sample_kb/
│       ├── company_it_handbook.md
│       └── service_desk_runbook.md
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
├── templates/
│   └── index.html
│
├── tests/
│   └── test_ingestion.py
│
├── uploads/
├── .env.example
├── Dockerfile
├── ingest_sample_kb.py
├── requirements.txt
├── run.py
└── README.md
```

---

## 6. Getting Started

### Step 1 — Create a virtual environment

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment variables

Create a `.env` file in the project root:

```env
# LLM API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# External Search
TAVILY_API_KEY=your_tavily_api_key_here

# Vector Database (Pinecone)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=fde-it-support-rag
PINECONE_NAMESPACE=company-it-kb

# LLM Models
GROQ_MODEL=openai/gpt-oss-20b
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Security
ADMIN_API_KEY=change-me-in-production

# Application Settings
APP_ENV=development
```

### Step 4 — Load the sample company knowledge base

```bash
python ingest_sample_kb.py
```

This runs the ingestion pipeline:

```
Company Documents → Load → Chunk Text → HuggingFace Embeddings → Pinecone Vector DB
```

### Step 5 — Run the application

```bash
python run.py
```

- App: `http://127.0.0.1:8000`
- API docs (Swagger): `http://127.0.0.1:8000/docs`

---

## 7. Demo Scenarios (What This Actually Proves)

### Demo A — Private KB Success
**Ask:** *"How do I connect to the company VPN from home?"*

```
Router → KB → Private KB Retrieval → KB Grade: GOOD → Generate from Private KB
```
**Point:** Trusted internal knowledge is used first — no unnecessary public web call.

### Demo B — Company Policy Question
**Ask:** *"Can IT support ask me to share my MFA code?"*

```
Router → KB → Private KB Retrieval → KB Grade: GOOD → Private KB Answer
```
**Point:** The model correctly answers using company-specific policy it was never trained on — this is the core value of RAG.

### Demo C — External / Current Information
**Ask:** *"What is the latest Microsoft Teams outage guidance?"*

```
Router → KB → Private KB Retrieval → KB Grade: WEAK
       → Tavily Search → Web Grade: GOOD → Web Answer
```
**Point:** The agent recognizes when its private data is insufficient and *chooses* another information source, rather than answering off irrelevant vectors.

### Demo D — Query Rewrite
**Ask a deliberately vague question:** *"My work communication app is acting strange after the new update. What should I do?"*

If both KB and the first external search come back weak, the workflow rewrites the query and retries — bounded by a retry guard to prevent infinite loops.

**Point:** Retrieval failure isn't treated as terminal failure — the agent can improve its own query.

### Demo E — Direct Conversation
**Ask:** *"Hello!"*

```
Router → DIRECT → Direct Answer
```
**Point:** Not every message deserves a vector search and a web search — the router filters that out up front.

---

## 8. Document Upload (Self-Service Knowledge Base)

The sidebar includes **Add Company Document**, authenticated with `ADMIN_API_KEY`.

Supported formats: `.pdf`, `.txt`, `.md`, `.docx`

```
Upload → Validate Type → Load Text → Recursive Chunking → Embeddings → Pinecone Indexing → Immediately Retrievable
```

This matters in a real deployment: the customer's IT team publishes new policies regularly, and they should never need to touch Python to keep the assistant current.

---

## 9. API Reference

### `GET /api/health`
Health check endpoint.

### `POST /api/chat`

**Request:**
```json
{
  "question": "How do I reset my company password?"
}
```

**Response:**
```json
{
  "answer": "...",
  "source_used": "private_kb",
  "trace": [
    "Router → KB",
    "Private KB retrieval → 4 chunks",
    "KB evidence grade → GOOD",
    "Answer generation → PRIVATE KB"
  ],
  "citations": []
}
```

The `trace` field is deliberately exposed — every answer comes with its own audit trail, so support staff (and engineers debugging the system) can see exactly *why* the agent answered the way it did.

### `POST /api/ingest`
Protected by the `X-Admin-Key` request header. Uploads a document and indexes its chunks into Pinecone.

---

## 10. Deployment

The application is containerized with **Docker** for reproducible builds and deployed on **Render** for managed, scalable hosting.

```bash
# Build the image
docker build -t it-copilot .

# Run locally
docker run -p 8000:8000 --env-file .env it-copilot
```

On Render, the same Docker image is deployed as a **Web Service**, with environment variables configured through Render's dashboard rather than a committed `.env` file.

---

## 11. Engineering Highlights

- **Evidence grading, not just retrieval** — every source (private and web) is judged for relevance before it's allowed to influence an answer, directly reducing hallucination risk.
- **Conditional routing over a linear pipeline** — the LangGraph state machine decides its own next step instead of following one fixed path for every query.
- **Bounded self-correction** — query rewriting with a retry guard lets the agent recover from a bad first attempt without risking infinite loops.
- **Transparency by design** — every response carries a `trace` of the decisions that produced it, which is what makes an agentic system debuggable and trustworthy in an enterprise setting.
- **Zero-code knowledge updates** — non-technical staff can extend the knowledge base through a secured upload endpoint, not a redeploy.
- **Production-shaped, not demo-shaped** — Dockerized, environment-configured, audit-logged, and deployed on Render, rather than left as a local notebook.
