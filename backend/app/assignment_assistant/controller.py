from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, io, base64, uuid
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

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
OUTPUT_FILE = "output.txt"
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
        # Save uploaded PDF
        pdf_path = os.path.join(TEMP_FOLDER, file.filename)
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # Convert PDF to images
        pages = convert_from_path(pdf_path, dpi=300)
        ocr_texts = []
        image_base64_list = []

        for i, page in enumerate(pages):
            img_path = os.path.join(TEMP_FOLDER, f"{os.path.splitext(file.filename)[0]}_page_{i+1}.png")
            page.save(img_path, "PNG")

            text = pytesseract.image_to_string(page, lang="eng").strip()
            ocr_texts.append(text)

            with open(img_path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            image_base64_list.append(img_b64)

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
            "pages_processed": len(pages),
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



# from fastapi import FastAPI, UploadFile, File
# from fastapi.responses import JSONResponse
# import os, io, base64
# from pdf2image import convert_from_path
# from PIL import Image
# import pytesseract
# from fastapi.middleware.cors import CORSMiddleware

# from model import get_client, get_deployment_name
# from prompts import get_supervision_prompt

# app = FastAPI(title="Handwritten Assignment Analyzer")

# origins = ["http://localhost:5173", "http://127.0.0.1:5173","http://10.10.20.151:5173"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# TEMP_FOLDER = "temp_images"
# OUTPUT_FILE = "output.txt"
# os.makedirs(TEMP_FOLDER, exist_ok=True)

# @app.post("/analyze-pdf/")
# async def analyze_pdf(file: UploadFile = File(...)):
#     """
#     Upload a handwritten PDF assignment -> extract text -> send to Azure OpenAI -> return AI feedback.
#     """
#     try:
#         # Save uploaded file
#         pdf_path = os.path.join(TEMP_FOLDER, file.filename)
#         with open(pdf_path, "wb") as f:
#             f.write(await file.read())

#         # Initialize client and model
#         client = get_client()
#         DEPLOYMENT_NAME = get_deployment_name()

#         # Step 1: Convert PDF to images
#         pages = convert_from_path(pdf_path, dpi=300)
#         print(f"Converted {len(pages)} pages from PDF.")

#         ocr_texts = []
#         image_base64_list = []

#         # Step 2: OCR + base64
#         for i, page in enumerate(pages):
#             img_path = os.path.join(TEMP_FOLDER, f"{os.path.splitext(file.filename)[0]}_page_{i+1}.png")
#             page.save(img_path, "PNG")

#             text = pytesseract.image_to_string(page, lang="eng").strip()
#             ocr_texts.append(text)

#             with open(img_path, "rb") as img_file:
#                 img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
#             image_base64_list.append(img_b64)

#         # Step 3: Save OCR and base64 to output file (for debugging)
#         with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#             for i, (txt, b64) in enumerate(zip(ocr_texts, image_base64_list)):
#                 f.write(f"----- PAGE {i+1} -----\n")
#                 f.write("Extracted Text:\n")
#                 f.write(txt + "\n\n")
#                 f.write("Base64 Encoded Image:\n")
#                 f.write(b64 + "\n\n")
#                 f.write("=" * 80 + "\n\n")

#         combined_text = "\n\n".join(ocr_texts)
#         safe_prompt = get_supervision_prompt(combined_text)

#         # Step 4: Call Azure OpenAI
#         response = client.chat.completions.create(
#             model=DEPLOYMENT_NAME,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": "You are an educational assistant that gives safe, respectful feedback to students based on their handwritten answers."
#                 },
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": safe_prompt},
#                         *[
#                             {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
#                             for img_b64 in image_base64_list
#                         ]
#                     ]
#                 }
#             ],
#             max_tokens=800,
#         )

#         ai_feedback = response.choices[0].message.content

#         return JSONResponse({
#             "status": "success",
#             "pages_processed": len(pages),
#             "ocr_text": combined_text,
#             "ai_feedback": ai_feedback
#         })

#     except Exception as e:
#         return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
