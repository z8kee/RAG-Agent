import streamlit as st, requests, time
API_URL_QUERY = "http://127.0.0.1:8001/query"
API_URL_SPEECH = "http://127.0.0.1:8000/speech"

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