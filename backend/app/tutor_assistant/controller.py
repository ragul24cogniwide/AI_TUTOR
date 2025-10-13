from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import re
import json
import uvicorn
from fastapi import APIRouter


from app.tutor_assistant.model import RetrivalChain


tutor_router = APIRouter(
    prefix="/tutor",  
    tags=["tutor"]    
)


class QueryRequest(BaseModel):
    session_id: str
    question: str
 
session_histories: Dict[str, List] = {}

@tutor_router.post("/ask")
async def ask_question(request: QueryRequest):
    session_id = request.session_id
    question = request.question.strip()

    if session_id not in session_histories:
        session_histories[session_id] = []

    history = session_histories[session_id]

    if not question:
        return {"response": "Please ask a valid question.", "images": [], "has_images": False, "type": "invalid"}

    if question.lower() == "clear":
        session_histories[session_id] = []
        return {"response": "History cleared.", "images": [], "has_images": False, "type": "cleared"}

    history.append(HumanMessage(content=question))
    retriver = RetrivalChain()
    retriver.get_documents() 
    chain = retriver.summarize_results()
    result = chain.invoke({"input": question, "chat_history": history})
    history.append(AIMessage(content=result["answer"]))
    answer_text = result['answer']
    images = []
    type = "answer"

    try:
        parsed = json.loads(answer_text)

        # Case: parsed is a JSON string (e.g. double stringified)
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                answer_text = parsed.strip()
                parsed = {}

        if isinstance(parsed, dict):
            answer_text = parsed.get("answer", "").strip()
            images_raw = parsed.get("images", [])
            type = parsed.get("type", "answer")
        else:
            # Fallback if not a dict
            answer_text = result['answer'].strip()
            images_raw = []
            type = "answer"

    except json.JSONDecodeError:
        # Not JSON at all
        answer_text = result['answer'].strip()
        images_raw = []
        type = "answer"

    # ✅ Extract only filenames from image URLs
    cleaned_images = []
    for image in images_raw:
        if isinstance(image, dict) and "url" in image:
            url_str = image["url"]
        else:
            url_str = str(image)

        match = re.search(r'/([^/]+\.(?:jpg|jpeg|png|gif))$', url_str, re.IGNORECASE)
        if match:
            cleaned_images.append(match.group(1))

    return {
        "response": answer_text,
        "images": cleaned_images,
        "has_images": len(cleaned_images) > 0,
        "type": type,
    }


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)