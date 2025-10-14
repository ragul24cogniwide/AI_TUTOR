from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage
from app.tutor_assistant.model import RetrivalChain
import json, re

# Create the router
tutor_router = APIRouter(
    prefix="/tutor",
    tags=["tutor"]
)

# Request model
class QueryRequest(BaseModel):
    session_id: str
    question: str
    subject: str

# 🧠 Session memory map — stores one RetrivalChain per user session
tutor_sessions: Dict[str, RetrivalChain] = {}

@tutor_router.post("/ask")
async def ask_question(request: QueryRequest):
    session_id = request.session_id.strip()
    question = request.question.strip()

    if not question:
        return {
            "response": "Please ask a valid question.",
            "images": [],
            "has_images": False,
            "type": "invalid",
        }

    # 🔄 "clear" command resets session memory
    if question.lower() == "clear":
        if session_id in tutor_sessions:
            del tutor_sessions[session_id]
        return {
            "response": "✅ Memory cleared for this session.",
            "images": [],
            "has_images": False,
            "type": "cleared",
        }

    # 🧩 Get or create a retrieval chain with memory for this session
    if session_id not in tutor_sessions:
        retriever = RetrivalChain(request.subject)
        retriever.get_documents()
        tutor_sessions[session_id] = retriever
    else:
        retriever = tutor_sessions[session_id]

    # 🧠 Ask the question (uses ConversationalRetrievalChain + memory)
    result = await retriever.chat(question)
    answer_text = result.strip()
    images_raw = []
    type = "answer"

    # Handle JSON structured responses (if your model returns JSON)
    try:
        parsed = json.loads(answer_text)
        if isinstance(parsed, dict):
            answer_text = parsed.get("answer", "").strip()
            images_raw = parsed.get("images", [])
            type = parsed.get("type", "answer")
    except json.JSONDecodeError:
        pass

    # 🖼️ Extract image filenames if any
    # cleaned_images = []
    # for image in images_raw:
    #     if isinstance(image, dict) and "url" in image:
    #         url_str = image["url"]
    #     else:
    #         url_str = str(image)
    #     match = re.search(r'/([^/]+\.(?:jpg|jpeg|png|gif))$', url_str, re.IGNORECASE)
    #     if match:
    #         cleaned_images.append(match.group(1))

    return {
        "response": answer_text,
        "images": images_raw,
        "has_images": len(images_raw) > 0,
        "type": type,
    }
