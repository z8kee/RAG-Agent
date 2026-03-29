// Note: Change this to your Azure URL later. 
// For now, it points to your local main.py server.
const API_BASE_URL = "http://127.0.0.1:8080"; 

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const recordBtn = document.getElementById('record-btn');

let mediaRecorder;
let audioChunks = [];

function appendMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender === 'user' ? 'user-msg' : 'bot-msg');
    msgDiv.textContent = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
}

// 1. Handling Text Queries
sendBtn.addEventListener('click', async () => {
    const question = userInput.value.trim();
    if (!question) return;

    appendMessage(question, 'user');
    userInput.value = '';

    try {
        const response = await fetch(`${API_BASE_URL}/rag/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                emotion: "Neutral", // Default emotion for typed text
                confidence: 1.0
            })
        });

        if (!response.ok) throw new Error("API Request Failed");
        const data = await response.json();
        appendMessage(data.answer, 'bot');

    } catch (error) {
        console.error(error);
        appendMessage("Sorry, I couldn't reach the server.", 'bot');
    }
});

// Allow pressing "Enter" to send
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendBtn.click();
});

// 2. Handling Audio Recording
recordBtn.addEventListener('mousedown', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const formData = new FormData();
            formData.append("file", audioBlob, "recording.webm");

            appendMessage("🎙️ Processing audio...", 'user');

            try {
                // Step A: Send audio to /speech endpoint
                const speechRes = await fetch(`${API_BASE_URL}/audio/speech`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!speechRes.ok) throw new Error("Speech API Failed");
                const speechData = await speechRes.json();
                
                appendMessage(`(Transcribed: "${speechData.text}") [Emotion: ${speechData.emotion}]`, 'user');

                // Step B: Send transcribed text to /query endpoint
                const queryRes = await fetch(`${API_BASE_URL}/rag/query`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: speechData.text,
                        emotion: speechData.emotion,
                        confidence: speechData.confidence
                    })
                });

                if (!queryRes.ok) throw new Error("RAG API Failed");
                const queryData = await queryRes.json();
                
                appendMessage(queryData.answer, 'bot');

            } catch (error) {
                console.error(error);
                appendMessage("Sorry, there was an error processing your audio.", 'bot');
            }
        };

        mediaRecorder.start();
        recordBtn.classList.add('recording');
    } catch (err) {
        console.error("Microphone access denied:", err);
        alert("Please allow microphone permissions.");
    }
});

recordBtn.addEventListener('mouseup', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        recordBtn.classList.remove('recording');
    }
});