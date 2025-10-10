import os
from typing import Dict, List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document


class Embedder:
    def __init__(self, persist_dir="data/chroma_db"):
        self.persist_dir = persist_dir
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def run(self, all_docs: Dict[str, List[Document]]):
        for subject_key, documents in all_docs.items():
            print(f"Embedding {subject_key}: {len(documents)} docs")
            
            persist_path = os.path.join(self.persist_dir, subject_key)
            db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=persist_path
            )
            db.persist()