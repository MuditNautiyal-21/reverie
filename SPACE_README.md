---
title: Reverie API
emoji: 📖
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# Reverie API

Backend for [Reverie](https://github.com/) — a personal memory engine that
answers natural-language questions about a journal with warm, cited replies.

The frontend lives on Vercel and calls this Space at `/ask`.

## Endpoints

- `GET /health` — liveness probe
- `POST /ask` — `{ "question": str, "top_k"?: int }` returns
  `{ "answer": str, "citations": [...], "candidates_considered": int }`

## Secrets

Set in **Settings → Variables and secrets**:

- `GROQ_API_KEY` — get one at https://console.groq.com/keys
- `DATABASE_URL` — Supabase Postgres connection string (Session pooler) with
  the `vector` extension enabled

The repo, the data, and the deploy steps are documented at the upstream
GitHub project.
