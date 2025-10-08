import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class Chunker:
    def __init__(self, base_path="output/book", chunk_size=600, overlap=100):
        self.base_path = base_path
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        self.all_docs = {}

    def run(self):
        """Run chunking process for all subject folders"""
        for subject_folder in os.listdir(self.base_path):
            subject_path = os.path.join(self.base_path, subject_folder)

            if not os.path.isdir(subject_path):
                continue

            subject_docs = []
            for root, _, files in os.walk(subject_path):
                for file in files:
                    if file.endswith(".md"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read()

                        chunks = self.text_splitter.split_text(text)
                        subject_docs.extend([
                            {
                                "page_content": chunk,
                                "metadata": {"book": subject_folder, "source": file_path}
                            }
                            for chunk in chunks
                        ])

            self.all_docs[subject_folder] = subject_docs
            print(f"{subject_folder}: {len(subject_docs)} chunks created")

        self._save()

    def _save(self):
        """Save chunks to JSON instead of pickle"""
        os.makedirs("data", exist_ok=True)
        with open("data/chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.all_docs, f, ensure_ascii=False, indent=2)

        print("\n📂 All chunks saved to data/chunks.json")
