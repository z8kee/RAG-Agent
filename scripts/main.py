from fastapi import FastAPI
from store import app as rag_app
from speechapi import app as speech_app

app = FastAPI(title="TechRAG Extension Backend")

app.mount("/rag", rag_app)
app.mount("/audio", speech_app)