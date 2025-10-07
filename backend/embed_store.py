import pickle
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


with open("all_docs.pkl", "rb") as f:
    all_docs = pickle.load(f)


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


for subject, docs in all_docs.items():
    print(f"Creating Chroma DB for {subject} with {len(docs)} docs...")

    db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=f"chroma_db/{subject}"
    )
    db.persist()

print("All embeddings saved into Chroma DB locally")
