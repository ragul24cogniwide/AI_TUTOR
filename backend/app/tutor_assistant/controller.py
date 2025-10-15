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
    buttons = []
    correct_answer = False

    # Handle JSON structured responses (if your model returns JSON)
    try:
        parsed = json.loads(answer_text)
        print("parsed",parsed)
        if isinstance(parsed, dict):
            answer_text = parsed.get("answer", "").strip()
            images_raw = parsed.get("images", [])
            type = parsed.get("type", "answer")
            buttons = parsed.get("buttons", [])
            correct_answer = parsed.get("correct_answer", False)

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
        "buttons": buttons,
        "correct_answer": correct_answer,
        # "images": images_raw,
        # "has_images": len(images_raw) > 0,
        # "type": type,
    }


@tutor_router.get("/get-initial-response/{subject}")
async def get_initial_response(subject: str):
    if subject == "maths":
        return {
            "response": "<strong>I'm Trained with the below topics Please ask me about them.</strong>",
            "data":[
            {  "title": "Large Numbers Around Us"},
            {  "title": "Arithmetic Expressions" },
            {  "title": "A Peek Beyond the Point" },
            {  "title": "Expressions using Letter-Numbers" },
            {  "title": "Parallel and Intersecting Lines" },
            {  "title": "Number Play" },
            {  "title": "A Tale of Three Intersecting Lines" },
            {  "title": "Working with Fractions" },
            ]

            }
    if subject == "english":
        return {
            "response": "<strong>I'm Trained with the below topics Please ask me about them.</strong>",
            "data":[
  {
    "unit": "Unit 1: Learning Together",
    "chapters": [
      { "title": "The Day the River Spoke", "page": 1 },
      { "title": "Try Again", "page": 16 },
      { "title": "Three Days to See", "page": 28 },
    ],
  },
  {
    "unit": "Unit 2: Wit and Humour",
    "chapters": [
      { "title": "Animals, Birds, and Dr. Dolittle", "page": 43 },
      { "title": "A Funny Man", "page": 59 },
      { "title": "Say the Right Thing", "page": 70 },
    ],
  },
  {
    "unit": "Unit 3: Dreams and Discoveries",
    "chapters": [
      { "title": "My Brother’s Great Invention", "page": 91 },
      { "title": "Paper Boats", "page": 109 },
      { "title": "118", "page": 118 }, 
    ],
  },
  {
    "unit": "Unit 4: Travel and Adventure",
    "chapters": [
      { "title": "The Tunnel", "page": 139 },
      { "title": "Travel", "page": 157 },
      { "title": "Conquering the Summit", "page": 166 },
    ],
  },
  {
    "unit": "Unit 5: Bravehearts",
    "chapters": [
      { "title": "A Homage to Our Brave Soldiers", "page": 179 },
      { "title": "My Dear Soldiers", "page": 199 },
      { "title": "Rani Abbakka", "page": 206 },
    ],
  }
            ]
        }
