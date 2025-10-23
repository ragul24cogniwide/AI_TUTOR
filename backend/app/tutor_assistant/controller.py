from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage
from app.tutor_assistant.model import RetrievalChain
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
    prompt: bool
    model:str
    custom_prompt: str = ""

# 🧠 Session memory map — stores one RetrivalChain per user session
tutor_sessions: Dict[str, RetrievalChain] = {}

@tutor_router.post("/ask")
async def ask_question(request: QueryRequest):
    session_id = request.session_id.strip()
    question = request.question.strip()

    if not question:
        return {"response": "Please ask a valid question.", "buttons": [], "correct_answer": False, "hint": "", "type": "invalid"}

    if question.lower() == "clear":
        if session_id in tutor_sessions:
            del tutor_sessions[session_id]
        return {"response": "✅ Memory cleared for this session.", "buttons": [], "correct_answer": False, "hint": "", "type": "cleared"}

    # Create or reuse retrieval chain
    if session_id not in tutor_sessions:
        retriever = RetrievalChain(request.subject, request.prompt,request.model,request.custom_prompt)
        retriever.get_documents()
        tutor_sessions[session_id] = retriever
    else:
        retriever = tutor_sessions[session_id]

    # Ask the question
    result_raw = await retriever.chat(question)
    print("raw data:", result_raw)

    # Try to extract structured JSON from markdown format
    cleaned_json_str = re.sub(r'```json\s*([\s\S]*?)\s*```', r'\1', result_raw)

    try:
        result = json.loads(cleaned_json_str)
        # Structured JSON response
        parsed_result = {
            "response": result.get("answer", "").strip(),
            "correct_answer": result.get("correct_answer", False),
            "quick_replies": result.get("quick_replies", []),
        }
    except json.JSONDecodeError:
        # Fallback: Raw string as plain response
        parsed_result = {
            "response": result_raw.strip(),
            "correct_answer": False,
            "quick_replies": [],
        }

    return parsed_result


@tutor_router.get("/get-initial-response/{subject}")
async def get_initial_response(subject: str):
    if subject == "maths":
        return {
            "response": "<strong>I'm Trained with the below topics Please ask me about them.</strong>",
            "data":[   
            {"title":"Large Numbers and their properties (Exact and Approximate Values)"},
            {"title":"Arithmetic Expressions and Algebra using Letter Numbers (Simplification, Formulas, Patterns)"},
            {"title":"Decimal Numbers (Place Value, Notation, Units of Measurement, Operations)"},
            {"title":"Advanced Operations with Fractions (Multiplication, Division, Area connection)"},
            {"title":"Geometry: Properties of Parallel and Intersecting Lines (Transversals, Angles)"},
            {"title":"Geometry: Construction and Properties of Triangles (Angle Sum, Exterior Angles, Altitudes)"},
            {"title":"Number Play (Sequences like Virahānka Fibonacci Numbers, Magic Squares)"}
         ]
        }
    if subject == "english":
        return {
            "response": "<strong>I'm Trained with the below topics Please ask me about them.</strong>",
            "data":[
  {
    "Unit_No": "1",
    "Unit_Name": "Learning Together",
    "Lesson_Name": "The Day the River Spoke",
    "Grammar_Topics": [
      "Sentence Completion",
      "Onomatopoeia",
      "Fill in the blanks",
      "Preposition"
    ]
  },
  {
    "Unit_No": "1",
    "Unit_Name": "Learning Together",
    "Lesson_Name": "Try Again",
    "Grammar_Topics": [
      "Phrases",
      "Metaphor and Simile"
    ]
  },
  {
    "Unit_No": "1",
    "Unit_Name": "Learning Together",
    "Lesson_Name": "Three Days to See",
    "Grammar_Topics": [
      "Modal Verbs",
      "Descriptive Paragraph"
    ]
  },
  {
    "Unit_No": "2",
    "Unit_Name": "Wit and Humour",
    "Lesson_Name": "Animals, Birds, and Dr. Dolittle",
    "Grammar_Topics": [
      "Compound Words",
      "Palindrome",
      "Verbs (Present Perfect Tense)",
      "Notice Writing"
    ]
  },
  {
    "Unit_No": "2",
    "Unit_Name": "Wit and Humour",
    "Lesson_Name": "A Funny Man",
    "Grammar_Topics": [
      "Phrasal Verbs",
      "Adverbs and Prepositions"
    ]
  },
  {
    "Unit_No": "2",
    "Unit_Name": "Wit and Humour",
    "Lesson_Name": "Say the Right Thing",
    "Grammar_Topics": [
      "Suffix",
      "Verb Forms",
      "Tense (Present Continuous/Present Perfect Continuous)",
      "Kinds of Sentences"
    ]
  },
  {
    "Unit_No": "3",
    "Unit_Name": "Dreams & Discoveries",
    "Lesson_Name": "My Brother's Great Invention",
    "Grammar_Topics": [
      "Onomatopoeia",
      "Binomials (Conjunction)",
      "Phrasal Verb",
      "Idioms",
      "Verbs (Simple Past & Past Perfect)"
    ]
  },
  {
    "Unit_No": "3",
    "Unit_Name": "Dreams & Discoveries",
    "Lesson_Name": "Paper Boats",
    "Grammar_Topics": [
      "Opposites (Antonyms)",
      "Diary Entry"
    ]
  },
  {
    "Unit_No": "3",
    "Unit_Name": "Dreams & Discoveries",
    "Lesson_Name": "North, South, East, West",
    "Grammar_Topics": [
      "Associate Words with Meanings",
      "Subject-Verb Agreement",
      "Letter (Leave Application)"
    ]
  },
  {
    "Unit_No": "4",
    "Unit_Name": "Travel and Adventure",
    "Lesson_Name": "The Tunnel",
    "Grammar_Topics": [
      "Phrases",
      "Onomatopoeia",
      "Punctuation",
      "Descriptive Paragraph Writing"
    ]
  },
  {
    "Unit_No": "4",
    "Unit_Name": "Travel and Adventure",
    "Lesson_Name": "Travel",
    "Grammar_Topics": [
      "Onomatopoeia"
    ]
  },
  {
    "Unit_No": "4",
    "Unit_Name": "Travel and Adventure",
    "Lesson_Name": "Conquering the Summit",
    "Grammar_Topics": [
      "Phrases",
      "Correct Parts of Speech",
      "Article",
      "Formal Letter"
    ]
  },
  {
    "Unit_No": "5",
    "Unit_Name": "Bravehearts",
    "Lesson_Name": "A Homage to Our Brave Soldiers",
    "Grammar_Topics": [
      "Prefix and Root Words",
      "Main Clause",
      "Subordinate Clause",
      "Subordinating Conjunctions",
      "Collocations"
    ]
  },
  {
    "Unit_No": "5",
    "Unit_Name": "Bravehearts",
    "Lesson_Name": "My Dear Soldiers",
    "Grammar_Topics": [
      "Fill in the blanks (Spelling)",
      "Speech (Direct & Indirect Speech)"
    ]
  }
]
        }
    

class TopicFinder(BaseModel):
    subject: str
    query: str


@tutor_router.post("/get-important-topics")
async def get_response_template(topic_finder: TopicFinder):
    print(topic_finder.query)
    print(topic_finder.subject)
    retriever= RetrievalChain(topic_finder.subject)
    retriever.get_documents()
    result = retriever.get_important_topics(topic_finder.query)
    return [doc.page_content for doc in result]



