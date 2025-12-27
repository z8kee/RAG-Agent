import faiss, numpy as np
import requests, os
from feedparsing import *
from tokenisation import chunk_text
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, UploadFile, File
import tempfile
from textrecog import TextRecogApp
from pydantic import BaseModel

SYSTEM_PROMPT = f"""
You are a retrieval-grounded assistant.
Use the provided context to answer, give comprehensive answers, dont mention the provided context, just act like you already specialise in giving tech news.
If the answer is not in the context, say you do not know.
"""

DIM = 384

index = faiss.IndexFlatL2(DIM)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
app = FastAPI(title="TechBot")

docs = []

def embed(texts):
    vectors = embedder.encode(texts, convert_to_numpy=True)

    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)

    return vectors.astype("float32")

def add_documents(chunks, metadata):
    vectors = embed(chunks)
    print("Vectors shape:", vectors.shape)
    index.add(vectors)
    docs.extend(
        [{"text": c, "meta": metadata} for c in chunks]
    )

arts = fetch_articles()
for art in arts:
    chunks = chunk_text(art["text"])
    chunks = [c for c in chunks if len(c.strip()) > 25]

    if not chunks:
        continue

    add_documents(
        chunks,
        metadata={
            "title": art["title"],
            "source": art["source"]
        }
    )
    
def retrieve(query_embedding, k=5):
    distances, indices = index.search(query_embedding, k)
    return [docs[i] for i in indices[0]]


def generate_answer(query, contexts, confidence, emotion):
    context_text = "\n\n".join(c["text"] for c in contexts)

    api_key = os.getenv("OPEN_API_KEY")
    base_url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    emotion_hint = ""

    confidenceword = "High confidence" if confidence >= 0.7 else ("Mid confidence" if confidence >= 0.4 else ("Low confidence")) 
    
    if emotion:
            emotion_hint = f"\nDont mention user emotion.. User emotion: {emotion} (Confidence: {confidence:.2f})"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + emotion_hint},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
    ]

    payload = {"model": "gpt-4o-mini", "messages": messages}
    resp = requests.post(base_url, json=payload, headers=headers)
    
    if resp.status_code != 200:
        raise RuntimeError(f"Chat completion failed: {resp.status_code} {resp.text}")
    
    data = resp.json()
    
    return data.get("choices", [{}])[0].get("message", {}).get("content")

class QueryRequest(BaseModel):
    question: str
    emotion: str
    confidence: float

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

@app.post("/query", response_model=QueryResponse)
def ask(request: QueryRequest):   
    q_emb = embed([request.question])
    retrieved_docs = retrieve(q_emb)
    answer = generate_answer(request.question, retrieved_docs, request.confidence, request.emotion)
    sources = list({d["meta"]["source"] for d in retrieved_docs})

    return {
        "answer": answer,
        "sources": sources
    }