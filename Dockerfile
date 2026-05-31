FROM python:3.12-slim

# Hugging Face Spaces run containers as a non-root user with UID 1000 and a
# writable home at /home/user. Setting HOME and the HF cache there keeps the
# sentence-transformers download (pre-baked below) usable at runtime.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/user/.cache/huggingface \
    PORT=7860

RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# System deps kept minimal. libgomp1 is needed by torch wheels at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=user:user requirements.txt ./
RUN pip install -r requirements.txt

# Warm the embedding model into the image so the first /ask request does not
# pay the download + load cost.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY --chown=user:user app ./app

USER user
EXPOSE 7860

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "7860"]
