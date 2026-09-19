FROM python:3.11-slim

WORKDIR /app

# System deps for pymupdf and yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the ONNX embedding model (all-MiniLM-L6-v2, ~79.3 MB) at build
# time so it's baked into the image. This avoids downloading it on every
# first boot into the ephemeral /root/.cache/chroma/ directory, which was
# causing the embedding function to fail/timeout on the first /chat request.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Entrypoint: run ingest if chroma_db is empty, then start server
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
