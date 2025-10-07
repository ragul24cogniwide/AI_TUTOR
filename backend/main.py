from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json


# FastAPI app
app = FastAPI(title="AI Tutor RAG API")

# Enable CORS for frontend
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embeddings for querying
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load persisted Chroma DB
math8_db = Chroma(
    persist_directory="chroma_db/math8",
    embedding_function=embeddings
)
retriever = math8_db.as_retriever(search_kwargs={"k": 3})
print("Retriever loaded:", retriever)

# Initialize Groq LLM
llm = ChatGroq(
    model="groq/compound",
    api_key="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",
    temperature=0.7
)

# Fixed prompt template - simpler, without JSON formatting requirement
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a helpful AI tutor. Answer the user's question clearly and concisely based on the provided context.

Context from documents:
{context}

Question: {question}

Answer:"""
)

# Build RAG QA chain with correct input variable mapping
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={
        "prompt": prompt,
        "verbose": False
    }
)

# Pydantic model for request
class QueryRequest(BaseModel):
    session_id: str
    question: str

# In-memory session store
session_store: Dict[str, List[Dict[str, str]]] = {}

# POST endpoint
@app.post("/ask")
async def ask_question(request: QueryRequest):
    session_id = request.session_id
    question = request.question.strip()
    
    if not question:
        return {"response": "Please ask a valid question.", "images": []}

    history = session_store.get(session_id, [])

    try:
        # Call the QA chain with correct input key "query"
        result = qa({"query": question})
        
        # Extract answer text
        answer_text = result.get("result", "")
        
        # Collect images from source documents
        images = []
        for doc in result.get("source_documents", []):
            if "image_url" in doc.metadata:
                url = doc.metadata["image_url"]
                if url not in [img.get("url") for img in images]:
                    images.append({"url": url})
        
        # Store history
        history.append({"query": question, "answer": answer_text})
        session_store[session_id] = history
        
        return {
            "response": answer_text,
            "images": images,
            "has_images": len(images) > 0
        }
    
    except Exception as e:
        print(f"Error processing question: {str(e)}")
        return {
            "response": f"An error occurred: {str(e)}",
            "images": [],
            "has_images": False
        }

@app.get("/")
async def root():
    return {"message": "AI Tutor RAG API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}