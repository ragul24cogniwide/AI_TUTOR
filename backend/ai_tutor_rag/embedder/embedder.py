import os
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document


class Embedder:
    def __init__(self, json_path="data/chunks.json", persist_dir="data/chroma_db"):
        self.json_path = json_path
        self.persist_dir = persist_dir
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def run(self):
        """Create Chroma DB from chunks.json"""
        with open(self.json_path, "r", encoding="utf-8") as f:
            all_docs = json.load(f)

        for subject, docs in all_docs.items():
            print(f"Creating Chroma DB for {subject} with {len(docs)} docs...")
            documents = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in docs]

            db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=os.path.join(self.persist_dir, subject)
            )
            db.persist()

        print("✅ All embeddings saved into Chroma DB locally")
