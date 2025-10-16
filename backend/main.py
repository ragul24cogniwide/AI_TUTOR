from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.tutor_assistant.controller import tutor_router
from app.assignment_assistant.controller import assign_route
import uvicorn
from app.tutor_assistant.model import TutorAssistant
from fastapi.staticfiles import StaticFiles


app = FastAPI()

origins = ["http://localhost:5173", "http://127.0.0.1:5173","http://10.10.20.151:5173","https://schooldigitalised.cogniwide.com:6443"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
os.makedirs("app/tutor_assistant/output/images", exist_ok=True)
os.makedirs("app/assignment_assistant/pdf_images", exist_ok=True)

app.mount(
    "/app/tutor_assistant/output/images",
    StaticFiles(directory="app/tutor_assistant/output/images"),
    name="images"
)
app.mount(
    "/app/assignment_assistant/pdf_images",
    StaticFiles(directory="app/assignment_assistant/pdf_images"),
    name="pdf_images"
)
app.include_router(tutor_router)
app.include_router(assign_route)

# tutor_assistant = TutorAssistant()
# tutor_assistant.load_file()


if __name__ == "__main__":
    print('SERVER STARTED...')
    uvicorn.run(app, host="0.0.0.0", port=8000)