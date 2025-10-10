from chunker.chunker import Chunker
from embedder.embedder import Embedder
from api.server import RAGServer
import uvicorn


if __name__ == "__main__":
    # Step 1: Chunk documents
    chunker = Chunker()
    all_docs = chunker.run()

    # Step 2: Generate embeddings
    embedder = Embedder()
    embedder.run(all_docs)

    # Step 3: Start API Server

    server = RAGServer()
    uvicorn.run(server.app, host="0.0.0.0", port=8000)