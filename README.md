# AI-Powered CV Screener

An end-to-end AI system that generates realistic fake CVs and allows recruiters to query them using natural language through a RAG-powered chat interface.

Built with **Python**, **n8n**, **Supabase pgvector** and **OpenAI**.

---

## Demo

Ask questions like:
- *"Who has experience with Python?"*
- *"Which candidate graduated from UPC?"*
- *"Summarize the profile of Carlos Martinez"*
- *"Which candidates know Docker and GCP?"*

The system retrieves the most semantically relevant CV chunks and answers based strictly on the CV content.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  INDEXING PIPELINE                   │
│  (runs once)                                         │
│                                                      │
│  PDF Files → Extract Text → Chunk → Embed → Supabase│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  CHAT PIPELINE                       │
│  (runs on every message)                             │
│                                                      │
│  User Question → Embed → Supabase similarity search │
│       → Retrieve top 20 chunks → GPT-4o-mini        │
│       → Answer grounded in CV data                  │
└─────────────────────────────────────────────────────┘
```

Both pipelines are built in **n8n** with no custom backend code required.

---

## Project Structure

```
AI-Powered-CV-Screener/
├── generate_cvs.py              # CV generation script
├── requirements.txt
├── .env.example
├── generated_cvs/               # 30 generated PDF CVs
│   └── candidates_metadata.json # Structured data for all candidates
├── n8n_workflows/
│   ├── cv_indexer.json          # n8n indexing workflow (import & run once)
│   └── cv_chat.json             # n8n chat workflow (import & activate)
└── README.md
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key — [platform.openai.com](https://platform.openai.com/api-keys)
- Supabase account — [supabase.com](https://supabase.com) (free tier works)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ssanchis/AI-Powered-CV-Screener
cd AI-Powered-CV-Screener
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

`.env.example`:
```
OPENAI_API_KEY=sk-...
```

### 4. Generate the CVs

```bash
python generate_cvs.py
```

This generates 30 realistic fake CVs in `generated_cvs/` covering 15 roles and 10 nationalities. 

### 5. Set up Supabase

In your Supabase project, go to **SQL Editor** and run:

```sql
-- Enable vector extension
create extension if not exists vector;

-- Create table
create table cv_documents (
  id bigserial primary key,
  filename text,
  candidate_name text,
  content text,
  embedding vector(1536),
  metadata jsonb
);

-- Create similarity search function
create or replace function match_documents (
  query_embedding vector(1536),
  match_count int default 10
) returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    cv_documents.id,
    cv_documents.content,
    cv_documents.metadata,
    1 - (cv_documents.embedding <=> query_embedding) as similarity
  from cv_documents
  order by cv_documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

### 6. Start n8n

```bash
npx n8n
# Opens at http://localhost:5678
```

### 7. Import and run the indexing workflow

1. In n8n go to **Workflows → Import**
2. Import `n8n_workflows/cv_indexer.json`
3. Add your credentials (OpenAI API key + Supabase URL and secret key)
4. Copy the generated CVs to the n8n files directory:
```bash
cp generated_cvs/*.pdf ~/.n8n-files/
```
5. Execute the workflow once — this populates Supabase with embeddings

### 8. Import and activate the chat workflow

1. Import `n8n_workflows/cv_chat.json`
2. Add the same credentials
3. Toggle the workflow to **Active**
4. Copy the **Production URL** from the chat trigger node
5. Open the URL in your browser — the chat interface is ready

---

## How it works

### CV Generation
The `generate_cvs.py` script chains three services:
1. **GPT-4o-mini** generates structured candidate data as JSON (name, experience, skills, education, certifications) 
2. **DiceBear API** provides a unique avatar image for each candidate (free, no API key)
3. **Python PDF rendering** builds a professional single-page PDF layout

### RAG Pipeline
The indexing workflow extracts text from each PDF, splits it into ~3 chunks, and stores each chunk with its embedding and metadata (filename, email, phone) in Supabase. 

### Chat Interface
The n8n AI Agent receives each message, queries Supabase for the most relevant CV chunks, and passes them as context to GPT-4o-mini. A strict system prompt prevents hallucination — the model is instructed to only answer based on explicitly retrieved text and always cite the source.

