from fastapi import FastAPI, UploadFile, File
import shutil, os
from textrecog import TextRecogApp

# Instantiate the speech+emotion helper once at startup to avoid reloading
# heavy models on every request
app = FastAPI()
emotionrecog = TextRecogApp()

@app.post("/speech")
async def speechtoemotion(file: UploadFile = File(...)):
    # Save the uploaded file to a temporary path for processing
    path = f"temp_{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Use the shared TextRecogApp to transcribe and predict emotion
    text = emotionrecog.save_and_transcribe(path)
    emotion = emotionrecog.detect_emotion(text)

    # Clean up temporary file
    os.remove(path)

    return {
        "text": text,
        "emotion": emotion["label"],
        "confidence": emotion["confidence"]
    }