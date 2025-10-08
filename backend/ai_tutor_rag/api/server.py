from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json
import os


class RAGServer:
    def __init__(self, persist_base="data/chroma_db"):
        self.app = FastAPI(title="AI Tutor RAG API")
        self.persist_base = persist_base
        self._setup_cors()

        # Shared embeddings + LLM
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = ChatGroq(
            model="groq/compound",
            api_key="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",
            temperature=0.7
        )

        # Load system prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self.session_store: Dict[str, List[Dict[str, str]]] = {}
        self._setup_routes()

    def _setup_cors(self):
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.mount("/backend/ai_tutor_rag/output/book", StaticFiles(directory="output"), name="output")

    def _build_qa_chain(self, book: str):
        """Build QA chain for a given book"""
        chroma_dir = os.path.join(self.persist_base, book)
        if not os.path.exists(chroma_dir):
            raise ValueError(f"No Chroma DB found for book '{book}' in {chroma_dir}")

        retriever = Chroma(
            persist_directory=chroma_dir,
            embedding_function=self.embeddings
        ).as_retriever(search_kwargs={"k": 3})

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self.system_prompt
        )

        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )

    def _setup_routes(self):
        @self.app.post("/ask")
        async def ask_question(request: QueryRequest):
            session_id = request.session_id
            book = request.book
            question = request.question.strip()

            if not question:
                return {"response": "Please ask a valid question.", "images": []}

            # Build QA for selected book
            qa_chain = self._build_qa_chain(book)
            result = qa_chain.invoke({"query": question})

            try:
                parsed = json.loads(result["result"])
                answer_text = parsed.get("answer", "")
                images = parsed.get("images", [])
            except json.JSONDecodeError:
                answer_text = result["result"]
                images = []

            # Store session
            history = self.session_store.get(session_id, [])
            history.append({"question": question, "answer": answer_text, "book": book})
            self.session_store[session_id] = history

            return {"response": answer_text, "images": images, "has_images": len(images) > 0}


class QueryRequest(BaseModel):
    session_id: str
    book: str     # <--- NEW field (ex: "math7", "math8")
    question: str
