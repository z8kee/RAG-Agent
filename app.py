import streamlit as st, requests, time
API_URL_QUERY = "http://127.0.0.1:8001/query"
API_URL_SPEECH = "http://127.0.0.1:8000/speech"

# Start FastAPI backends when Streamlit starts (runs once per session)
import socket
import multiprocessing

def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.5)
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass

def _start_uvicorn(module: str, port: int):
    # spawn a separate process to avoid blocking Streamlit
    def _run():
        import uvicorn
        uvicorn.run(f"{module}:app", host="127.0.0.1", port=port, log_level="info")

    p = multiprocessing.Process(target=_run, daemon=True)
    p.start()
    return p


if "_apis_started" not in st.session_state:
    # start speechapi on 8000
    if not _port_in_use(8000):
        try:
            st.session_state["_speech_proc"] = _start_uvicorn("speechapi", 8000)
        except Exception:
            pass

    # start store (RAG) on 8001
    if not _port_in_use(8001):
        try:
            st.session_state["_store_proc"] = _start_uvicorn("store", 8001)
        except Exception:
            pass

    st.session_state["_apis_started"] = True

    def _wait_for_apis(timeout: int = 30, poll_interval: float = 0.5) -> bool:
        endpoints = [API_URL_QUERY, API_URL_SPEECH]
        start = time.time()

        while time.time() - start < timeout:
            all_up = True
            for url in endpoints:
                try:
                    requests.get(url, timeout=1)

                except Exception:
                    all_up = False
                    break

            if all_up:
                return True

            time.sleep(poll_interval)

        return False

    with st.spinner("Starting backends, waiting for APIs to become available... (Please wait up to 2 minutes)"):
        ready = _wait_for_apis(timeout=120)

    if not ready:
        st.warning("Some backends did not start within the timeout; features may be limited.")

    st.set_page_config(page_title="TechRAGBot", layout="centered")

st.title("Tech News Agent")
st.caption("Retrieval Augmented Agent")

# Initialize message history in the session (preserves across interaction)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render stored chat messages
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


question = st.chat_input("Enter a message to continue...")
audio = st.audio_input("Press to talk, Press to send...")

if question:
    # Append user's question to the session history and display it
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Send the question to the RAG backend `/query` endpoint
    with st.spinner("Thinking..."):
        response = requests.post(
            API_URL_QUERY,
            json={"question": question, "emotion": "", "confidence": 0},
            timeout=120,
        )

    if response.status_code == 200:
        data = response.json()

        # Store assistant response and sources in history
        st.session_state.messages.append({
            "role": "assistant",
            "content": data["answer"],
            "sources": data["sources"],
        })

        # Animate assistant reply for a nicer UX
        with st.chat_message("assistant"):
            placeholder = st.empty()
            animated = ""
            for ch in data["answer"]:
                animated += ch
                placeholder.markdown(animated)
                time.sleep(0.01)

            # Display sources returned by the backend
            st.markdown("### Sources")
            for src in data["sources"]:
                st.write(f"- {src}")
    else:
        st.error("Backend error")

elif audio:
    # When audio is provided, package it as a file-like mapping for requests
    files = {
        "file": (audio.name, audio.getvalue(), audio.type),
    }

    # Upload audio to the speech/emotion backend which returns the
    # transcribed text, detected emotion label and confidence
    with st.spinner("Listening..."):
        speech_resp = requests.post(API_URL_SPEECH, files=files)

    if speech_resp.status_code != 200:
        st.error("Speech backend error")

    speech_data = speech_resp.json()
    text = speech_data["text"]
    emotion = speech_data["emotion"]
    confidence = speech_data["confidence"]

    # Add the transcribed text to the chat and query the RAG backend
    st.session_state.messages.append({"role": "user", "content": text})

    with st.chat_message("user"):
        st.markdown(text)

    with st.spinner("Thinking..."):
        rag_resp = requests.post(
            API_URL_QUERY,
            json={"question": text, "emotion": emotion, "confidence": confidence},
            timeout=120,
        )

    if rag_resp.status_code != 200:
        st.error("RAG backend error")
        st.stop()

    rag_data = rag_resp.json()

    st.session_state.messages.append({
        "role": "assistant",
        "content": rag_data["answer"],
        "sources": rag_data["sources"]
        })
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        animated = ""
        for ch in rag_data["answer"]:
            animated += ch
            placeholder.markdown(animated)
            time.sleep(0.01)

        st.markdown("### Sources")
        for src in rag_data["sources"]:
            st.write(f"- {src}")

