# Reverie

<img width="1875" height="1255" alt="hero" src="https://github.com/user-attachments/assets/f8144afa-bd5b-41d7-b3e1-860dd302d696" />

A personal memory engine. You point it at a body of personal writing, ask a
question in plain language, and it answers warmly with citations instead of
returning a flat list of matches.

The public demo runs on a synthetic journal so no real private writing is ever
exposed. The character is composite. The arc is invented. Everything else about
the system is real.

## What it does

One thing. A person types a question like "what was I anxious about last
spring" or "when did I sound happiest." The system retrieves the entries that
are most relevant, asks a model to write a short reply grounded only in those
entries, and renders the reply alongside the specific journal passages it drew
from. The reply addresses the writer in second person. The citations sit
underneath, quieter, so the answer leads and the memories support it.

## How it works

<img width="1037" height="688" alt="landing_state" src="https://github.com/user-attachments/assets/8c5a7b35-6df8-4568-999c-cde119a4e718" />


Each entry is enriched once with mood, themes, tags, and a one-line summary by
a single LLM call. The enriched corpus is embedded locally with
sentence-transformers (`all-MiniLM-L6-v2`, 384 dimensions) and stored in
Postgres with the `pgvector` extension. An HNSW index on cosine distance backs
retrieval.

A question is embedded the same way. The retriever pulls more candidates than
it strictly needs, then the model is given the full text of each candidate
along with the question. The model does two things in one call: it decides
which entries actually answer the question, and it writes the reply. Citations
are attached server-side from the fetched rows, never from anything the model
emits, which means the model cannot invent journal text.

The LLM sits behind a small provider interface. Groq's free tier is the
default. Swapping to Gemini or Anthropic is one new class and a config value.

## Stack

Python, FastAPI, Uvicorn on the backend. Groq (Llama 3.3 70B) for the model.
sentence-transformers locally for embeddings. Postgres with `pgvector` for
storage and retrieval, hosted on Supabase's free tier. React with Vite and
Tailwind on the frontend. A short Python script reports retrieval quality
against a labelled question set.

## Run it locally

You need Python 3.11 or newer, Node 18 or newer, a Groq API key, and a Postgres
database with the `vector` extension enabled. Supabase is the simplest path.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env                   # fill in GROQ_API_KEY and DATABASE_URL

python -m app.enrich                   # writes data/enriched.json
python -m app.index                    # embeds and upserts into Postgres
uvicorn app.api:app --reload           # serves /ask on :8000
```

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env                   # adjust VITE_API_BASE_URL if needed
npm run dev
```

Open `http://localhost:5173`. Type a question or click one of the example
prompts.

## Configuration

| Variable          | Default                                       | Notes                                                                |
|-------------------|-----------------------------------------------|----------------------------------------------------------------------|
| `LLM_PROVIDER`    | `groq`                                        | Provider name. Adding another is a subclass plus a branch.           |
| `LLM_MODEL`       | `llama-3.3-70b-versatile`                     | Passed through to the provider.                                      |
| `GROQ_API_KEY`    | required for `groq`                           | Get one at https://console.groq.com/keys                             |
| `DATABASE_URL`    | required                                      | Postgres connection string with `pgvector` enabled.                  |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2`      | Override at your own risk; must match `EMBEDDING_DIM`.               |
| `EMBEDDING_DIM`   | `384`                                         | Must match the model's output dimension.                             |

## Evaluation

A small labelled question set lives at `data/eval_questions.json`. The script
runs pure retrieval (no model in the loop) and reports per-question hit and
recall at k, plus an overall hit rate and mean recall.

```bash
python -m app.eval
```

On the eight-question set at k=5, the current numbers are a hit rate of 1.00
and a mean recall of 0.72. Every question finds at least one of its expected
entries in the top five. Some questions pull in all of their expected entries,
some pull in two of three, and a couple lose entries whose connection to the
question is implicit rather than spelled out in the text. That gap is real and
worth being honest about: a small bi-encoder will favour shared vocabulary over
inference. The answer layer compensates by giving the model the full text of a
larger candidate pool so it can pick what actually fits.

## At scale

This stack is sized for a single synthetic corpus on a free tier. For a real
deployment with many users, many corpora, and a real ingest cadence, the
shape that makes sense is BigQuery for the entries and their enrichment as the
system of record, Cloud Run for the API, Cloud Tasks for asynchronous
enrichment and reindexing, and a managed vector store. The provider interface,
the over-fetch-then-rerank pattern, and the schema all carry over. The local
embedding step becomes a worker, and the eval script becomes a CI check.

## Project layout

```
app/
  config.py          environment + paths
  ingest.py          load raw entries
  enrich.py          LLM call per entry → enriched.json
  embeddings.py      local sentence-transformers wrapper
  db.py              psycopg + pgvector setup, schema bootstrap
  index.py           embed + upsert into memories
  search.py          semantic search CLI and function
  answer.py          retrieval + grounded answer with citations
  api.py             FastAPI surface
  eval.py            retrieval evaluation
  llm/
    provider.py      base interface, get_provider()
    groq_provider.py Groq implementation
data/
  entries.json       the synthetic journal
  enriched.json      generated by app.enrich
  eval_questions.json
frontend/
  src/
    App.jsx          single screen
    components/      AskBox, Examples, Answer, Citations, etc.
    api.js           thin client around /ask
```
