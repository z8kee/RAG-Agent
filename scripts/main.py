from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from store import app as rag_app
from speechapi import app as speech_app

app = FastAPI(title="TechRAG Extension Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
app.mount("/rag", rag_app)
app.mount("/audio", speech_app)