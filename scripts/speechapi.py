from fastapi import FastAPI, UploadFile, File
import shutil, os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import nltk
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
from textrecog import TextRecogApp

# instantiate the speech+emotion helper once at startup to avoid reloading
# heavy models on every request
app = FastAPI()
emotionrecog = TextRecogApp()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/speech")
async def speechtoemotion(file: UploadFile = File(...)):
    #  temporary path used for saving file
    path = f"temp_{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # use the shared TextRecogApp to transcribe and predict emotion
    text = emotionrecog.save_and_transcribe(path)
    emotion = emotionrecog.detect_emotion(text)

    # Clean up temporary file
    os.remove(path)

    return {
        "text": text,
        "emotion": emotion["label"],
        "confidence": emotion["confidence"]

    }

