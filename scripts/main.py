from fastapi import FastAPI
from store import app as rag_app
from speechapi import app as speech_app

# This is your master app
app = FastAPI(title="TechRAG Extension Backend")

# Mount your existing apps under specific paths
app.mount("/rag", rag_app)
app.mount("/audio", speech_app)

# Note: Your endpoints will now be accessible at:
# /rag/query
# /audio/speech