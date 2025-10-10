import os
from typing import Dict, List
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

    def run(self) -> Dict[str, List[Document]]:
        for grade_folder in os.listdir(self.base_path):
            grade_path = os.path.join(self.base_path, grade_folder)
            if not os.path.isdir(grade_path):
                continue

            for subject_folder in os.listdir(grade_path):
                subject_path = os.path.join(grade_path, subject_folder)
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
                            for chunk in chunks:
                                subject_docs.append(
                                    Document(
                                        page_content=chunk,
                                        metadata={
                                            "grade": grade_folder,
                                            "subject": subject_folder,
                                            "source": file_path
                                        }
                                    )
                                )

                key = f"{grade_folder}/{subject_folder}"
                self.all_docs[key] = subject_docs
                print(f"{key}: {len(subject_docs)} chunks")

        return self.all_docs