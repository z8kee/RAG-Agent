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
        uvicorn.run(
            f"{module}:app", 
            host="127.0.0.1", 
            port=port, 
            log_level="warning", 
            access_log=False
        )

    p = multiprocessing.Process(target=_run, daemon=True)
    p.start()
    return p


# Check health WITHOUT a blocking while loop
speech_ready = _port_in_use(8000)
rag_ready = _port_in_use(8001)
