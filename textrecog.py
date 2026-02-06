import whisper, cv2, re, os, time, pickle
import numpy as np
from keras.models import load_model
from scipy.io.wavfile import write
from sklearn import preprocessing
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sentence_transformers import SentenceTransformer

class TextRecogApp:
    def __init__(self):
        # Models & preprocessors
        self.cv = pickle.load(open("textrecogitems/CountVectorizer.pkl", "rb"))
        self.le = pickle.load(open("textrecogitems/encoder.pkl", "rb"))
        self.ps = PorterStemmer()
        self.model = load_model('textrecogitems/stt_model.h5')
        self.modeltext = whisper.load_model("small")

        # tokenises each word and removes stopwords for easier emotion detection
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
        top_labels = self.le.inverse_transform(top_idx[:top_k])
        top_probs = probs[top_idx[:top_k]]

        best_idx = int(top_idx[0])
        confidence = float(probs[best_idx])
        label = self.le.inverse_transform([best_idx])[0] 

        return {"label": label, 
                "confidence": confidence,

        }
