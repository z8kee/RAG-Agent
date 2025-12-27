import tiktoken

tokeniser = tiktoken.get_encoding("cl100k_base")

def chunk_text(text, max_tokens=500, overlap=50):
    tokens = tokeniser.encode(text)
    chunks = []
    i = 0

    while i < len(tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(tokeniser.decode(chunk))
        i += max_tokens - overlap - 2

    return chunks


