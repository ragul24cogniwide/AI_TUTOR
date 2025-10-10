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

from prompt import Prompts


class QueryRequest(BaseModel):
    session_id: str
    grade: str
    subject: str
    question: str


class RAGServer:
    def __init__(self, persist_base="data/chroma_db"):
        self.app = FastAPI(title="AI Tutor RAG API")
        self.persist_base = persist_base
        self._setup_cors()

        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = ChatGroq(
            model="groq/compound",
            api_key="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",
            temperature=0.7
        )
        self.session_store: Dict[str, List[Dict[str, str]]] = {}
        self._setup_routes()

    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.mount("/backend/ai_tutor_rag/output/book", StaticFiles(directory="output/book"), name="output")

    def _build_qa_chain(self, grade: str, subject: str):
        chroma_dir = os.path.join(self.persist_base, grade, subject)
        if not os.path.exists(chroma_dir):
            return None

        db = Chroma(
            persist_directory=chroma_dir,
            embedding_function=self.embeddings
        )
        
        retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        try:
            prompt_text = Prompts.get_prompt(grade, subject)
        except ValueError:
            return None

        prompt = PromptTemplate(input_variables=["context", "question"], template=prompt_text)
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )

    def _setup_routes(self):
        @self.app.post("/ask")
        async def ask_question(request: QueryRequest):
            session_id = request.session_id
            grade = request.grade.lower()
            subject = request.subject.lower()
            question = request.question.strip()

            if not question:
                return {"response": "Please ask a valid question.", "images": []}

            qa_chain = self._build_qa_chain(grade, subject)
            if qa_chain is None:
                return {"response": f"Sorry, I can only answer questions for {grade} {subject}.", "images": []}

            result = qa_chain.invoke({"query": question})
            if not result or not result.get("result"):
                return {"response": f"Sorry, I can only answer questions for {grade} {subject}.", "images": []}

            try:
                parsed = json.loads(result["result"])
                answer_text = parsed.get("answer", "")
                images = parsed.get("images", [])
            except json.JSONDecodeError:
                answer_text = result["result"]
                images = []

            history = self.session_store.get(session_id, [])
            history.append({"question": question, "answer": answer_text, "grade": grade, "subject": subject})
            self.session_store[session_id] = history

            return {"response": answer_text, "images": images, "has_images": len(images) > 0}
