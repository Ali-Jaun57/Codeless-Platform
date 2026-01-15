

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel


# from openai import OpenAI

# from dotenv import load_dotenv
# import os

# load_dotenv()

# openai_api_key = os.getenv("OPENAI_API_KEY")
# if not openai_api_key:
#     raise ValueError("OPENAI_API_KEY not found in environment variables")

# app = FastAPI(title="Codeless API")

# app.add_middleware(
#   CORSMiddleware,
#   allow_origins=["http://localhost:3000"],
#   allow_credentials=True,
#   allow_methods=["*"],
#   allow_headers=["*"],
# )

# # OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# if not client.api_key:
#   raise RuntimeError("OPENAI_API_KEY not set")

# class GenerateRequest(BaseModel):
#   prompt: str

# class GenerateResponse(BaseModel):
#   code: str
#   language: str = "python"  # Default, can detect later

# # @app.post("/generate-code", response_model=GenerateResponse)
# # async def generate_code(request: GenerateRequest):
# #   if not request.prompt.strip():
# #     raise HTTPException(status_code=400, detail="Prompt required")

# #   try:
# #     response = client.chat.completions.create(
# #       model="gpt-4o",
# #       messages=[
# #         {
# #           "role": "system",
# #           "content": "You are an expert coder. Generate ONE complete, high-quality single file for the user request. Use best practices, comments, error handling. Detect language from prompt. Output ONLY the code block with ```language"
# #         },
# #         {"role": "user", "content": request.prompt}
# #       ],
# #       temperature=0.5,
# #       max_tokens=2000,
# #     )
# #     raw = response.choices[0].message.content.strip()

# #     # Extract code block    
# #     if "```" in raw:
# #       code = raw.split("```")[1].split("\n", 1)[1].rsplit("```", 1)[0].strip()
# #       language = raw.split("```")[1].split("\n", 1)[0].strip() or "text"
# #     else:
# #       code = raw
# #       language = "text"

# #     return {"code": code, "language": language}
# #   except Exception as e:
# #     raise HTTPException(status_code=500, detail=str(e))

# @app.post("/generate-project")
# async def generate_project(request: GenerateRequest):
#   if not request.prompt.strip():
#     raise HTTPException(status_code=400, detail="Prompt required")

#   # try:
#   #   response = client.chat.completions.create(
#   #     model="gpt-4o",
#   #     messages=[
#   #       {
#   #         "role": "system",
#   #         "content": "You are an expert full-stack coder. Generate a complete project for the user request. Output ONLY a JSON array of files: [{ \"path\": \"file/path.js\", \"content\": \"code\" }]. Use relative paths, include package.json if needed, README.md with instructions. No explanation."
#   #       },
#   #       {"role": "user", "content": request.prompt}
#   #     ],
#   #     response_format={ "type": "json_object" },
#   #     temperature=0.5,
#   #   )
#   #   raw = response.choices[0].message.content.strip()

#   #   import json
#   #   files = json.loads(raw)

#   #   if "files" in files:
#   #     files = files["files"]  # If wrapped

#   #   return {"files": files}
#   # except Exception as e:
#   #   raise HTTPException(status_code=500, detail=str(e))

#   try:
#     response = client.chat.completions.create(
#       model="gpt-4o",
#       messages=[
#         {
#           "role": "system",
#           "content": "You are an expert full-stack coder. Generate a complete project as multiple files. Output ONLY valid JSON: {\"files\": [{\"path\": \"relative/path/file.js\", \"content\": \"full code\"}]}. Include package.json, README.md. No explanation or markdown."
#         },
#         {"role": "user", "content": request.prompt}
#       ],
#       response_format={ "type": "json_object" },
#       temperature=0.5,
#       max_tokens=4000,
#     )
#     raw = response.choices[0].message.content.strip()
#     print("Raw OpenAI response:", raw)  # Debug log

#     data = json.loads(raw)

#     # Flexible: get files from root or wrapped
#     files = data.get("files", [])
#     if not files and isinstance(data, list):
#       files = data  # If direct array

#     if not files:
#       raise ValueError("No files in response")

#     return {"files": files}
#   except Exception as e:
#     print("OpenAI error:", str(e))  # Debug
#     raise HTTPException(status_code=500, detail=str(e))

# @app.get("/health")
# async def health():
#   return {"status": "ok", "message": "Codeless backend ready!"}

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json  # ← Added at top

load_dotenv()

app = FastAPI(title="Codeless API")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class GenerateRequest(BaseModel):
  prompt: str

class File(BaseModel):
  path: str
  content: str

class GenerateResponse(BaseModel):
  files: list[File]

@app.post("/generate-project", response_model=GenerateResponse)
async def generate_project(request: GenerateRequest):
  if not request.prompt.strip():
    raise HTTPException(status_code=400, detail="Prompt required")

  try:
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {
          "role": "system",
          "content": "You are an expert full-stack coder. Generate a complete project as multiple files. Output ONLY valid JSON: {\"files\": [{\"path\": \"relative/path/file.js\", \"content\": \"full code\"}]}. Include package.json, README.md with setup. No explanation or markdown."
        },
        {"role": "user", "content": request.prompt}
      ],
      response_format={ "type": "json_object" },
      temperature=0.5,
      max_tokens=4000,
    )
    raw = response.choices[0].message.content.strip()
    print("Raw OpenAI response:", raw)  # Debug

    data = json.loads(raw)

    files = data.get("files", [])
    if not files and isinstance(data, list):
      files = data

    if not files:
      raise ValueError("No files in response")

    return {"files": files}
  except Exception as e:
    print("Error:", str(e))
    raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
  return {"status": "ok"}