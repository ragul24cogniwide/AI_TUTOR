import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    )

def get_deployment_name():
    return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")




# import os
# import base64
# from pdf2image import convert_from_path
# from openai import AzureOpenAI
# from PIL import Image
# import io
# import pytesseract

# # ----------------- CONFIG -----------------
# AZURE_OPENAI_ENDPOINT = "https://cogniassit-genai.openai.azure.com"
# AZURE_OPENAI_API_KEY = "f0ca889dec9940dfa6caad23eedf4b7b"
# DEPLOYMENT_NAME = "gpt-4o-mini"  # or your deployed model name
# PDF_PATH = "demo1 (1).pdf"  # Input PDF file path
# # ------------------------------------------

# # Initialize Azure OpenAI client
# client = AzureOpenAI(
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
#     api_key=AZURE_OPENAI_API_KEY,
#     api_version="2025-01-01-preview"  # or latest version supported for multimodal
# )

# # Step 1. Convert PDF to images
# pages = convert_from_path(PDF_PATH, dpi=300)
# print(f"Converted {len(pages)} pages from PDF.")

# # Step 2. OCR each page and encode image
# ocr_texts = []
# image_base64_list = []

# for i, page in enumerate(pages):
#     # OCR text extraction
#     text = pytesseract.image_to_string(page, lang='eng')
#     ocr_texts.append(text.strip())

#     # Convert image to base64
#     buffered = io.BytesIO()
#     page.save(buffered, format="PNG")
#     img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
#     image_base64_list.append(img_b64)

# # Step 3. Combine extracted text
# combined_text = "\n\n".join(ocr_texts)

# safe_prompt = f"""
# The following text was extracted from a student's handwritten assignment.

# Your role: analyze it in a helpful and constructive educational way.

# Please do these tasks:
# 1. Summarize what the student wrote.
# 2. Comment briefly on clarity and completeness.
# 3. Ask three educational follow-up questions about the topic.

# OCR extracted text:
# {combined_text}
# """

# response = client.chat.completions.create(
#     model=DEPLOYMENT_NAME,
#     messages=[
#         {
#             "role": "system",
#             "content": "You are an educational assistant that gives safe, respectful feedback to students based on their handwritten answers."
#         },
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": safe_prompt},
#                 *[
#                     {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
#                     for img_b64 in image_base64_list
#                 ]
#             ]
#         }
#     ],
#     max_tokens=800,
# )


# print("\n--- SUPERVISION REPORT ---")
# print(response.choices[0].message.content)