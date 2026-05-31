# Deploy

Three pieces: a Postgres database on Supabase (already provisioned), a Docker
backend on a Hugging Face Space, and a static React frontend on Vercel. The
order below assumes you have run the corpus build locally once already, so the
`memories` table in Supabase is populated.

## 0. Preflight

Before you start, confirm the local stack works end to end. The deploy is a
move, not a debug.

```bash
python -m app.enrich      # data/enriched.json exists
python -m app.index       # memories table has 35 rows in Supabase
uvicorn app.api:app       # /ask answers a local curl
```

If any of those fail, fix them first.

## 1. Backend on Hugging Face Spaces

Spaces give you a free always-on container with HTTPS and no card required.

1. Go to https://huggingface.co/new-space.
2. Owner = your account. Space name = `reverie-api` (or anything you like).
   License = MIT. SDK = **Docker**. Choose **Blank** template. Hardware = the
   default free CPU. Visibility = **Public**.
3. Create the Space. You will land on an empty repo page.
4. Push the backend files to that repo. From the project root:

   ```bash
   # The Space gave you a git URL like:
   #   https://huggingface.co/spaces/<you>/reverie-api
   git remote add space https://huggingface.co/spaces/<you>/reverie-api
   git push space main
   ```

   Spaces wants a top-level `README.md` with docker frontmatter. The one this
   repo ships at `SPACE_README.md` is that file. Either rename it on the Space
   side, or before pushing, do:

   ```bash
   git checkout -b deploy
   cp SPACE_README.md README.md         # overwrites the project README
   git add README.md && git commit -m "deploy: Space README"
   git push space deploy:main
   ```

   The `Dockerfile` and `.dockerignore` at the repo root are what Spaces will
   actually build.

5. While the first build runs (it pre-downloads the embedding model, so expect
   a few minutes), open **Settings → Variables and secrets** on the Space and
   add:

   - `GROQ_API_KEY` = your Groq key
   - `DATABASE_URL` = the Supabase Session pooler URI, password URL-encoded if
     it contains special characters

   Mark both as **Secret**, not Variable. Saving them triggers a restart.

6. When the Space status goes green, hit the API:

   ```bash
   curl https://<you>-reverie-api.hf.space/health
   # {"status":"ok"}

   curl -X POST https://<you>-reverie-api.hf.space/ask \
        -H "Content-Type: application/json" \
        -d '{"question":"how did I feel about Maya after she left"}'
   ```

   You should see a JSON response with `answer` and `citations`. If `/health`
   works but `/ask` errors, the most likely cause is a missing or wrong secret.
   Check the Space logs.

## 2. Frontend on Vercel

1. Push the whole repo to GitHub if it is not there already.
2. Go to https://vercel.com/new and import the GitHub repo.
3. On the import screen, set **Root Directory** to `frontend`. Vercel will
   detect Vite automatically. Build command `npm run build`, output `dist`.
4. Under **Environment Variables**, add:

   - `VITE_API_BASE_URL` = `https://<you>-reverie-api.hf.space`

   No trailing slash. Apply to Production, Preview, and Development.

5. Deploy. The first build takes about a minute.

6. Open the production URL Vercel gives you. Type a question or click an
   example prompt. The first request to the Space after it has been idle for a
   while may take ten or twenty seconds while the container wakes up.

## 3. After deploy

- Update `README.md` with the live URL once it is stable.
- Record a short screen capture of the demo for the application package.
- If you change the corpus, run `python -m app.enrich` and `python -m app.index`
  locally. The Space does not need to redeploy because the data lives in
  Supabase, not in the image.

## Troubleshooting

**CORS error in the browser.** The API ships with `allow_origins=["*"]` for
this reason. If you still see it, the response probably failed before CORS
headers were written. Check Space logs.

**`401` or `502` from `/ask`.** Almost always a missing or mistyped secret.
Open the Space settings, re-paste the value, save, wait for restart.

**Cold start feels slow.** Free Spaces sleep after a period of inactivity. The
embedding model is baked into the image so cold-start is bounded by container
start time, not by a model download.

**Password with `@` in `DATABASE_URL`.** URL-encode it as `%40`. Same for `:`,
`/`, `?`, `#`, `%`, `&`, `+`.
