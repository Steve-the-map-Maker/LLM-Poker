import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv("backend/.env")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
for m in genai.list_models():
    print(m.name)
