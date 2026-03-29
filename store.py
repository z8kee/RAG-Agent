import faiss, requests, os, shutil, nltk, whisper, re, pickle
from feedparsing import *
from tokenisation import chunk_text
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from keras.models import load_model
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

SYSTEM_PROMPT = f"""
You are a retrieval-grounded assistant.
Use the provided context to answer, give comprehensive answers, dont mention the provided context, just act like you already specialise in giving tech news.
If the answer is not in the context, say you do not know.
"""

# --- App Initialization ---
app = FastAPI(title="TechRAG Extension Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RAG Setup ---
DIM = 384
index = faiss.IndexFlatL2(DIM)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
docs = []

# --- Emotion Setup ---
class TextRecogApp:
    def __init__(self):
        self.cv = pickle.load(open("textrecogitems/CountVectorizer.pkl", "rb"))
        self.le = pickle.load(open("textrecogitems/encoder.pkl", "rb"))
        self.ps = PorterStemmer()
        self.model = load_model('textrecogitems/stt_model.h5')
        self.modeltext = whisper.load_model("small")
        self.stopwords = set(stopwords.words('english'))

    def preprocess_text(self, line):
        text = re.sub('[^a-zA-Z]', ' ', line)
        text = text.lower().split()
        text = [self.ps.stem(w) for w in text if w not in self.stopwords]
        return " ".join(text)
    
    def save_and_transcribe(self, audio_path): 
        result = self.modeltext.transcribe(audio_path)
        return result["text"]
       
    def detect_emotion(self, text, top_k=3):
        text = self.preprocess_text(text)
        array = self.cv.transform([text]).toarray()
        probs = self.model.predict(array)[0] 
        top_idx = probs.argsort()[::-1]
        best_idx = int(top_idx[0])
        return {"label": self.le.inverse_transform([best_idx])[0], "confidence": float(probs[best_idx])}

emotionrecog = TextRecogApp()

# --- Helper Functions ---
def embed(texts):
    vectors = embedder.encode(texts, convert_to_numpy=True)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    return vectors.astype("float32")

def add_documents(chunks, metadata):
    vectors = embed(chunks)
    index.add(vectors)
    docs.extend([{"text": c, "meta": metadata} for c in chunks])

def retrieve(query_embedding, k=5):
    distances, indices = index.search(query_embedding, k)
    return [docs[i] for i in indices[0]]

def generate_answer(query, contexts, confidence, emotion):
    context_text = "\n\n".join(c["text"] for c in contexts)
    api_key = os.environ.get("OPEN_API_KEY") # Fixed env var name
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    confidenceword = "High confidence" if confidence >= 0.7 else ("Mid confidence" if confidence >= 0.4 else "Low confidence") 
    emotion_hint = f"\nDont mention user emotion.. User emotion: {emotion} ({confidenceword}: {confidence:.2f})" if emotion else ""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + emotion_hint},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
    ]

    resp = requests.post("https://api.openai.com/v1/chat/completions", json={"model": "gpt-4o-mini", "messages": messages}, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Chat completion failed: {resp.status_code} {resp.text}")
    return resp.json().get("choices", [{}])[0].get("message", {}).get("content")

# --- Startup Scraping ---
arts = fetch_articles()
for art in arts:
    chunks = [c for c in chunk_text(art["text"]) if len(c.strip()) > 25]
    if chunks:
        add_documents(chunks, metadata={"title": art["title"], "source": art["source"]})

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    question: str
    emotion: str
    confidence: float

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryResponse)
def ask(request: QueryRequest):   
    retrieved_docs = retrieve(embed([request.question]))
    answer = generate_answer(request.question, retrieved_docs, request.confidence, request.emotion)
    return {"answer": answer, "sources": list({d["meta"]["source"] for d in retrieved_docs})}

@app.post("/speech")
async def speechtoemotion(file: UploadFile = File(...)):
    path = f"temp_{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    text = emotionrecog.save_and_transcribe(path)
    emotion = emotionrecog.detect_emotion(text)
    os.remove(path)
    return {"text": text, "emotion": emotion["label"], "confidence": emotion["confidence"]}