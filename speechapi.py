from fastapi import FastAPI, UploadFile, File
import shutil, os
from textrecog import TextRecogApp


app = FastAPI()
emotionrecog = TextRecogApp()

@app.post("/speech")
async def speechtoemotion(file: UploadFile = File(...)):
    path = f"temp_{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


    text = emotionrecog.save_and_transcribe(path)
    emotion = emotionrecog.detect_emotion(text)

    os.remove(path)

    return {
        "text": text,
        "emotion": emotion["label"],
        "confidence": emotion["confidence"]
    }