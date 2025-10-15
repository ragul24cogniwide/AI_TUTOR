from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, io, base64, uuid
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from docx import Document
from model import get_client, get_deployment_name
from prompts import get_supervision_prompt

app = FastAPI(title="Handwritten Assignment Interactive Assistant")

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_FOLDER = "temp_images"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# In-memory session storage
chat_sessions = {}  # { session_id: [messages] }

client = get_client()
DEPLOYMENT_NAME = get_deployment_name()


@app.post("/start-session/")
async def start_session(file: UploadFile = File(...)):
    """
    Upload handwritten PDF → start chat session → return first AI question.
    """
    try:
        filename = file.filename.lower()
        file_path = os.path.join(TEMP_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        ocr_texts = []
        image_base64_list = []
        pages_processed = 0 

        if filename.endswith(".pdf"):
           
            pages = convert_from_path(file_path, dpi=300)
            for i, page in enumerate(pages):
                img_path = os.path.join(TEMP_FOLDER, f"{os.path.splitext(filename)[0]}_page_{i+1}.png")
                page.save(img_path, "PNG")

                text = pytesseract.image_to_string(page, lang="eng").strip()
                ocr_texts.append(text)

                with open(img_path, "rb") as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
                image_base64_list.append(img_b64)

        elif filename.endswith(".docx"):
            from docx import Document
            doc = Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            doc_text = "\n".join(full_text)
            ocr_texts.append(doc_text)
            pages_processed = 1

        else:
            return JSONResponse({"status": "error", "message": "Unsupported file type. Upload PDF or DOCX."}, status_code=400)

        combined_text = "\n\n".join(ocr_texts)
        safe_prompt = get_supervision_prompt(combined_text)

        # Initialize session
        session_id = str(uuid.uuid4())
        session_messages = [
            {"role": "system", "content": "You are an educational assistant that gives safe, respectful feedback to students based on their handwritten answers."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": safe_prompt},
                    *[
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                        for img_b64 in image_base64_list
                    ]
                ]
            }
        ]
        chat_sessions[session_id] = session_messages

        # Get AI first response
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=session_messages,
            max_tokens=800
        )

        ai_reply = response.choices[0].message.content
        chat_sessions[session_id].append({"role": "assistant", "content": ai_reply})

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "pages_processed": pages_processed,
            "first_ai_message": ai_reply
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/send-message/")
async def send_message(session_id: str = Form(...), student_message: str = Form(...)):
    """
    Send student's reply → get next AI message → maintain session.
    """
    try:
        if session_id not in chat_sessions:
            return JSONResponse({"status": "error", "message": "Invalid session_id"}, status_code=400)

        session_messages = chat_sessions[session_id]

        # Append student's message
        session_messages.append({"role": "user", "content": student_message})

        # Get AI reply
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=session_messages,
            max_tokens=800
        )

        ai_reply = response.choices[0].message.content
        session_messages.append({"role": "assistant", "content": ai_reply})

        return JSONResponse({
            "status": "success",
            "ai_message": ai_reply
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/session-history/")
async def session_history(session_id: str):
    """
    Retrieve full chat history for a session.
    """
    if session_id not in chat_sessions:
        return JSONResponse({"status": "error", "message": "Invalid session_id"}, status_code=400)

    return JSONResponse({
        "status": "success",
        "history": chat_sessions[session_id]
    })


