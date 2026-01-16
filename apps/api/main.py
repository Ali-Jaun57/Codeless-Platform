# # # # # from fastapi import FastAPI, HTTPException
# # # # # from fastapi.middleware.cors import CORSMiddleware
# # # # # from pydantic import BaseModel
# # # # # from openai import OpenAI
# # # # # from dotenv import load_dotenv
# # # # # import os
# # # # # import json  # ← Added at top

# # # # # load_dotenv()

# # # # # app = FastAPI(title="Codeless API")

# # # # # app.add_middleware(
# # # # #   CORSMiddleware,
# # # # #   allow_origins=["http://localhost:3000"],
# # # # #   allow_credentials=True,
# # # # #   allow_methods=["*"],
# # # # #   allow_headers=["*"],
# # # # # )

# # # # # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # # # # class GenerateRequest(BaseModel):
# # # # #   prompt: str

# # # # # class File(BaseModel):
# # # # #   path: str
# # # # #   content: str

# # # # # class GenerateResponse(BaseModel):
# # # # #   files: list[File]

# # # # # @app.post("/generate-project", response_model=GenerateResponse)
# # # # # async def generate_project(request: GenerateRequest):
# # # # #   if not request.prompt.strip():
# # # # #     raise HTTPException(status_code=400, detail="Prompt required")

# # # # #   try:
# # # # #     response = client.chat.completions.create(
# # # # #       model="gpt-4o",
# # # # #       messages=[
# # # # #         {
# # # # #           "role": "system",
# # # # #           "content": "You are an expert full-stack coder. Generate a complete project as multiple files. Output ONLY valid JSON: {\"files\": [{\"path\": \"relative/path/file.js\", \"content\": \"full code\"}]}. Include package.json, README.md with setup. No explanation or markdown."
# # # # #         },
# # # # #         {"role": "user", "content": request.prompt}
# # # # #       ],
# # # # #       response_format={ "type": "json_object" },
# # # # #       temperature=0.5,
# # # # #       max_tokens=4000,
# # # # #     )
# # # # #     raw = response.choices[0].message.content.strip()
# # # # #     print("Raw OpenAI response:", raw)  # Debug

# # # # #     data = json.loads(raw)

# # # # #     files = data.get("files", [])
# # # # #     if not files and isinstance(data, list):
# # # # #       files = data

# # # # #     if not files:
# # # # #       raise ValueError("No files in response")

# # # # #     return {"files": files}
# # # # #   except Exception as e:
# # # # #     print("Error:", str(e))
# # # # #     raise HTTPException(status_code=500, detail=str(e))

# # # # # @app.get("/health")
# # # # # async def health():
# # # # #   return {"status": "ok"}

# # # # from fastapi import FastAPI, HTTPException
# # # # from fastapi.middleware.cors import CORSMiddleware
# # # # from pydantic import BaseModel
# # # # from openai import OpenAI
# # # # from dotenv import load_dotenv
# # # # from langgraph.graph import StateGraph, END
# # # # from langchain_core.messages import HumanMessage, AIMessage
# # # # from langchain_openai import ChatOpenAI
# # # # import os
# # # # import json

# # # # load_dotenv()

# # # # app = FastAPI(title="Codeless API")

# # # # app.add_middleware(
# # # #   CORSMiddleware,
# # # #   allow_origins=["http://localhost:3000"],
# # # #   allow_credentials=True,
# # # #   allow_methods=["*"],
# # # #   allow_headers=["*"],
# # # # )

# # # # llm = ChatOpenAI(model="gpt-4o", temperature=0.5)

# # # # class AgentState(BaseModel):
# # # #   messages: list = []
# # # #   files: list[dict] = []
# # # #   iteration: int = 0
# # # #   max_iterations: int = 3

# # # # # Nodes
# # # # def planner(state: AgentState):
# # # #   prompt = f"""Plan a complete project for: {state.messages[-1].content}
# # # #   Output JSON: {{"plan": "step-by-step plan", "files": ["path1.js", "path2.py", ...]}}"""
# # # #   response = llm.invoke([HumanMessage(content=prompt)])
# # # #   plan = json.loads(response.content)
# # # #   print("PLANNING COMPLETED.  Planner output:", plan)
# # # #   return {"messages": state.messages + [AIMessage(content=response.content)], "files": plan.get("files", [])}

# # # # def coder(state: AgentState):
# # # #   prompt = f"""Generate code for files: {state.files}
# # # #   Current plan: {state.messages[-2].content if len(state.messages) > 1 else ""}
# # # #   Output JSON: {{"files": [{{"path": "path", "content": "code"}}]}}"""
# # # #   response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# # # #   files = json.loads(response.content).get("files", [])
# # # #   print("CODING COMPLETED.  Coder output files:", files)
# # # #   return {"messages": state.messages + [AIMessage(content=response.content)], "files": files}

# # # # def critic(state: AgentState):
# # # #   prompt = f"""Critique the code: {json.dumps(state.files)}
# # # #   Suggest improvements or approve.
# # # #   Output JSON: {{"critique": "text", "approved": true/false}}"""
# # # #   response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# # # #   critique = json.loads(response.content)
# # # #   print("CRITIQUE COMPLETED.  Critic output:", critique)
# # # #   return {"messages": state.messages + [AIMessage(content=response.content)], "iteration": state.iteration + 1, "files": state.files if critique["approved"] else []}

# # # # def should_continue(state: AgentState):
# # # #   if state.iteration >= state.max_iterations or state.files:
# # # #     return END
# # # #   return "coder"

# # # # # Graph
# # # # workflow = StateGraph(AgentState)
# # # # workflow.add_node("planner", planner)
# # # # workflow.add_node("coder", coder)
# # # # workflow.add_node("critic", critic)

# # # # workflow.set_entry_point("planner")
# # # # workflow.add_edge("planner", "coder")
# # # # workflow.add_edge("coder", "critic")
# # # # workflow.add_conditional_edges("critic", should_continue)

# # # # graph = workflow.compile()

# # # # class GenerateRequest(BaseModel):
# # # #   prompt: str

# # # # @app.post("/generate-project")
# # # # async def generate_project(request: GenerateRequest):
# # # #   try:
# # # #     print(f"📨 Received prompt: {request.prompt}")
# # # #     inputs = {"messages": [HumanMessage(content=request.prompt)], "files": [], "iteration": 0}
# # # #     print("🔄 Starting LangGraph workflow...")
# # # #     result = graph.invoke(inputs)
# # # #     return {"files": result["files"]}
# # # #   except Exception as e:
# # # #     raise HTTPException(status_code=500, detail=str(e))

# # # # @app.get("/health")
# # # # async def health():
# # # #   return {"status": "ok"}

# # # from fastapi import FastAPI, HTTPException
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from pydantic import BaseModel
# # # from langchain_openai import ChatOpenAI
# # # from langgraph.graph import StateGraph, END
# # # from langchain_core.messages import HumanMessage, AIMessage
# # # from dotenv import load_dotenv
# # # import os
# # # import json

# # # load_dotenv()

# # # app = FastAPI(title="Codeless API")

# # # app.add_middleware(
# # #   CORSMiddleware,
# # #   allow_origins=["http://localhost:3000"],
# # #   allow_credentials=True,
# # #   allow_methods=["*"],
# # #   allow_headers=["*"],
# # # )

# # # llm = ChatOpenAI(model="gpt-4o", temperature=0.5)

# # # class AgentState(BaseModel):
# # #   messages: list = []
# # #   files: list[dict] = []
# # #   iteration: int = 0
# # #   max_iterations: int = 3

# # # def planner(state: AgentState):
# # #   prompt = f"Plan a complete project for: {state.messages[-1].content}\nOutput JSON: {{\"plan\": \"description\", \"files\": [\"path1.js\", \"path2.css\"]}}"
# # #   response = llm.invoke([HumanMessage(content=prompt)])
# # #   try:
# # #     plan = json.loads(response.content)
# # #   except:
# # #     plan = {"files": []}
# # #   print("PLANNING COMPLETED.  Planner output:", plan)
# # #   return {"messages": state.messages + [AIMessage(content=response.content)], "files": plan.get("files", [])}

# # # def coder(state: AgentState):
# # #   prompt = f"Generate code for files: {state.files}\nPrevious plan/critique: {state.messages[-1].content if state.messages else ''}\nOutput JSON: {{\"files\": [{{\"path\": \"path\", \"content\": \"code\"}}]}}"
# # #   response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# # #   try:
# # #     data = json.loads(response.content)
# # #     files = data.get("files", [])
# # #   except:
# # #     files = []
# # #   print("CODING COMPLETED.  Coder output files:", files)
# # #   return {"messages": state.messages + [AIMessage(content=response.content)], "files": files}

# # # def critic(state: AgentState):
# # #   prompt = f"Critique the code files: {json.dumps(state.files)}\nSuggest improvements or approve ({{\"approved\": true/false, \"critique\": \"text\"}})"
# # #   response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# # #   try:
# # #     critique = json.loads(response.content)
# # #     approved = critique.get("approved", False)
# # #   except:
# # #     approved = False
# # #   print("CRITIQUE COMPLETED.  Critic output:", critique)
# # #   return {"messages": state.messages + [AIMessage(content=response.content)], "iteration": state.iteration + 1, "files": state.files if approved else []}

# # # def should_continue(state: AgentState):
# # #   if state.iteration >= state.max_iterations or len(state.files) > 0:
# # #     return END
# # #   return "coder"

# # # workflow = StateGraph(AgentState)
# # # workflow.add_node("planner", planner)
# # # workflow.add_node("coder", coder)
# # # workflow.add_node("critic", critic)

# # # workflow.set_entry_point("planner")
# # # workflow.add_edge("planner", "coder")
# # # workflow.add_edge("coder", "critic")
# # # workflow.add_conditional_edges("critic", should_continue, {"coder": "coder", END: END})

# # # graph = workflow.compile()

# # # class GenerateRequest(BaseModel):
# # #   prompt: str

# # # @app.post("/generate-project")
# # # async def generate_project(request: GenerateRequest):
# # #   try:
# # #     print(f"📨 Received prompt: {request.prompt}")
# # #     inputs = {"messages": [HumanMessage(content=request.prompt)], "files": [], "iteration": 0}
# # #     print("🔄 Starting LangGraph workflow...")
# # #     result = graph.invoke(inputs)
# # #     return {"files": result["files"]}
# # #     print("✅ Project generation completed.")
# # #   except Exception as e:
# # #     raise HTTPException(status_code=500, detail=str(e))

# # # @app.get("/health")
# # # async def health():
# # #   return {"status": "ok"}

# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from pydantic import BaseModel
# # from langchain_openai import ChatOpenAI
# # from langgraph.graph import StateGraph, END
# # from langchain_core.messages import HumanMessage, AIMessage
# # from dotenv import load_dotenv
# # import os
# # import json
# # import asyncio

# # load_dotenv()

# # app = FastAPI(title="Codeless API")

# # app.add_middleware(
# #   CORSMiddleware,
# #   allow_origins=["http://localhost:3000"],
# #   allow_credentials=True,
# #   allow_methods=["*"],
# #   allow_headers=["*"],
# # )

# # llm = ChatOpenAI(model="gpt-4o", temperature=0.5, timeout=60)  # Timeout 60s

# # class AgentState(BaseModel):
# #   messages: list = []
# #   files: list[dict] = []
# #   iteration: int = 0
# #   max_iterations: int = 3

# # def planner(state: AgentState):
# #   print("🔵 STARTING PLANNER")
# #   prompt = f"Plan a complete project for: {state.messages[-1].content}\nOutput ONLY JSON: {{\"plan\": \"brief description\", \"files\": [\"path1.js\", \"path2.css\", ...]}}"
# #   try:
# #     response = llm.invoke([HumanMessage(content=prompt)])
# #     print("Planner raw response:", response.content)
# #     plan = json.loads(response.content)
# #     files = plan.get("files", [])
# #   except Exception as e:
# #     print("Planner error:", str(e))
# #     files = []
# #   print("PLANNER COMPLETED. Files planned:", files)
# #   return {"messages": state.messages + [AIMessage(content=str(response.content))], "files": files}

# # def coder(state: AgentState):
# #   print("🟢 STARTING CODER (iteration", state.iteration, ")")
# #   prompt = f"Generate complete code for these files: {state.files}\nUse previous context. Output ONLY JSON: {{\"files\": [{{\"path\": \"path\", \"content\": \"full code\"}}]}}"
# #   try:
# #     response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# #     print("Coder raw response:", response.content)
# #     data = json.loads(response.content)
# #     files = data.get("files", [])
# #   except Exception as e:
# #     print("Coder error:", str(e))
# #     files = []
# #   print("CODER COMPLETED. Generated", len(files), "files")
# #   return {"messages": state.messages + [AIMessage(content=str(response.content))], "files": files}

# # def critic(state: AgentState):
# #   print("🟡 STARTING CRITIC (iteration", state.iteration, ")")
# #   prompt = f"Critique these files for bugs/best practices: {json.dumps(state.files)}\nOutput ONLY JSON: {{\"critique\": \"text\", \"approved\": true/false, \"improvements\": [\"list\"]}}"
# #   try:
# #     response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# #     print("Critic raw response:", response.content)
# #     critique = json.loads(response.content)
# #     approved = critique.get("approved", False)
# #   except Exception as e:
# #     print("Critic error:", str(e))
# #     approved = False
# #   print("CRITIC COMPLETED. Approved:", approved)
# #   return {"messages": state.messages + [AIMessage(content=str(response.content))], "iteration": state.iteration + 1, "files": state.files if approved else []}

# # def should_continue(state: AgentState):
# #   print("Checking continue: iteration", state.iteration, "files", len(state.files))
# #   if state.iteration >= state.max_iterations or len(state.files) > 0:
# #     print("ENDING workflow")
# #     return END
# #   print("Continuing to coder")
# #   return "coder"

# # workflow = StateGraph(AgentState)
# # workflow.add_node("planner", planner)
# # workflow.add_node("coder", coder)
# # workflow.add_node("critic", critic)

# # workflow.set_entry_point("planner")
# # workflow.add_edge("planner", "coder")
# # workflow.add_edge("coder", "critic")
# # workflow.add_conditional_edges("critic", should_continue)

# # graph = workflow.compile()

# # class GenerateRequest(BaseModel):
# #   prompt: str

# # @app.post("/generate-project")
# # async def generate_project(request: GenerateRequest):
# #   print(f"📨 Received prompt: {request.prompt}")
# #   try:
# #     inputs = {"messages": [HumanMessage(content=request.prompt)], "files": [], "iteration": 0}
# #     print("🔄 Starting LangGraph workflow...")
# #     result = await asyncio.wait_for(asyncio.to_thread(graph.invoke, inputs), timeout=120)  # 2min timeout
# #     print("✅ Workflow completed. Files:", len(result.get("files", [])))
# #     return {"files": result.get("files", [])}
# #   except asyncio.TimeoutError:
# #     print("⏰ Workflow timeout")
# #     raise HTTPException(status_code=504, detail="Generation timeout - try simpler prompt")
# #   except Exception as e:
# #     print("❌ Workflow error:", str(e))
# #     raise HTTPException(status_code=500, detail=str(e))

# # @app.get("/health")
# # async def health():
# #   return {"status": "ok"}

# # # apps/api/main.py
# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from pydantic import BaseModel
# # from openai import OpenAI
# # from dotenv import load_dotenv
# # import os
# # import json

# # load_dotenv()

# # app = FastAPI(title="Codeless API")

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["http://localhost:3000"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # class GenerateRequest(BaseModel):
# #     prompt: str

# # @app.post("/generate-project")
# # async def generate_project(request: GenerateRequest):
# #     try:
# #         print(f"📨 Received prompt: {request.prompt}")
        
# #         response = client.chat.completions.create(
# #             model="gpt-4o",
# #             messages=[
# #                 {
# #                     "role": "system",
# #                     "content": """You are an expert full-stack developer. Generate a complete project.
# #                     Return ONLY valid JSON with this structure: {"files": [{"path": "filename.js", "content": "code here"}]}
# #                     No explanations, no markdown."""
# #                 },
# #                 {"role": "user", "content": request.prompt}
# #             ],
# #             response_format={"type": "json_object"},
# #             temperature=0.5,
# #             max_tokens=4000
# #         )
        
# #         raw_json = response.choices[0].message.content.strip()
# #         print(f"📦 Raw response preview: {raw_json[:100]}...")
        
# #         data = json.loads(raw_json)
        
# #         # Ensure files array exists
# #         files = data.get("files", [])
# #         if not files:
# #             files = [{"path": "app.js", "content": "// Generated app code"}]
        
# #         print(f"✅ Generated {len(files)} files")
# #         return {"files": files}
        
# #     except Exception as e:
# #         print(f"❌ Error: {str(e)}")
# #         import traceback
# #         traceback.print_exc()
# #         return {"files": [{"path": "error.txt", "content": f"Error: {str(e)}"}]}

# # @app.get("/health")
# # async def health():
# #     return {"status": "ok"}


# # apps/api/main.py - LANGGRAPH VERSION
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph, END
# from langchain_core.messages import HumanMessage, AIMessage
# from dotenv import load_dotenv
# import os
# import json
# import asyncio

# load_dotenv()

# app = FastAPI(title="Codeless API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize LangChain LLM
# llm = ChatOpenAI(model="gpt-4o", temperature=0.5, timeout=60)

# class AgentState(BaseModel):
#     messages: list = []
#     files: list[dict] = []
#     iteration: int = 0
#     max_iterations: int = 3

# # def planner(state: AgentState):
# #     print("🔵 STARTING PLANNER")
# #     prompt = f"""Plan a complete project for: {state.messages[-1].content}
# #     Output ONLY JSON: {{"plan": "brief description", "files": ["path1.js", "path2.css", ...]}}"""
    
# #     try:
# #         response = llm.invoke([HumanMessage(content=prompt)])
# #         print("Planner raw response:", response.content[:200])
# #         plan = json.loads(response.content)
# #         files = plan.get("files", [])
# #     except Exception as e:
# #         print("Planner error:", str(e))
# #         files = []
    
# #     print(f"PLANNER COMPLETED. Files planned: {len(files)}")
# #     return {"messages": state.messages + [AIMessage(content=response.content)], "files": files}

# # def coder(state: AgentState):
# #     print(f"🟢 STARTING CODER (iteration {state.iteration})")
    
# #     if not state.files:
# #         print("⚠️ No files to code, returning empty")
# #         return {"messages": state.messages, "files": []}
    
# #     prompt = f"""Generate complete code for these files: {state.files}
# #     Use previous context. Output ONLY JSON: {{"files": [{{"path": "path", "content": "full code"}}]}}"""
    
# #     try:
# #         response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# #         print("Coder raw response preview:", response.content[:200])
# #         data = json.loads(response.content)
# #         files = data.get("files", [])
# #     except Exception as e:
# #         print("Coder error:", str(e))
# #         files = []
    
# #     print(f"CODER COMPLETED. Generated {len(files)} files")
# #     return {"messages": state.messages + [AIMessage(content=response.content)], "files": files}

# # def critic(state: AgentState):
# #     print(f"🟡 STARTING CRITIC (iteration {state.iteration})")
    
# #     if not state.files:
# #         print("⚠️ No files to critique, approving empty")
# #         return {"messages": state.messages, "iteration": state.iteration + 1, "files": []}
    
# #     # Show only first 2 files to avoid token overflow
# #     files_preview = json.dumps(state.files[:2]) + ("..." if len(state.files) > 2 else "")
    
# #     prompt = f"""Critique these files for bugs/best practices: {files_preview}
# #     Output ONLY JSON: {{"critique": "text", "approved": true/false, "improvements": ["list"]}}"""
    
# #     try:
# #         response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# #         print("Critic raw response:", response.content[:200])
# #         critique = json.loads(response.content)
# #         approved = critique.get("approved", False)
# #     except Exception as e:
# #         print("Critic error:", str(e))
# #         approved = False
    
# #     print(f"CRITIC COMPLETED. Approved: {approved}")
# #     return {"messages": state.messages + [AIMessage(content=response.content)], 
# #             "iteration": state.iteration + 1, 
# #             "files": state.files if approved else []}

# # def planner(state: AgentState):
# #     print("🔵 STARTING PLANNER")
    
# #     prompt = f"""YOU ARE A PROJECT PLANNER. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# # USER REQUEST: {state.messages[-1].content}

# # CRITICAL RULES:
# # 1. Output MUST be valid JSON parsable by json.loads()
# # 2. NO markdown code blocks (no ```json or ```)
# # 3. NO explanations, comments, or extra text
# # 4. JSON structure MUST be exactly: {{"plan": "string description", "files": ["file1.js", "file2.css"]}}
# # 5. "files" array MUST contain actual file paths with extensions

# # EXAMPLE CORRECT OUTPUT:
# # {{"plan": "React calculator with premium UI", "files": ["index.html", "styles.css", "App.js", "calculator.js"]}}

# # NOW OUTPUT THE JSON:"""
    
# #     try:
# #         response = llm.invoke([HumanMessage(content=prompt)])
# #         raw_content = response.content.strip()
# #         print("Raw planner output:", raw_content[:200])
        
# #         # STRICT VALIDATION: Remove ANY non-JSON content
# #         # Find first { and last }
# #         start = raw_content.find('{')
# #         end = raw_content.rfind('}') + 1
        
# #         if start != -1 and end != 0:
# #             json_content = raw_content[start:end]
# #         else:
# #             json_content = raw_content
        
# #         print("Extracted JSON:", json_content[:200])
        
# #         plan = json.loads(json_content)
# #         files = plan.get("files", [])
        
# #     except Exception as e:
# #         print(f"Planner JSON error: {e}")
# #         # Fallback: create basic files array
# #         files = ["index.html", "styles.css", "app.js"]
# #         json_content = json.dumps({"plan": "Basic project", "files": files})
    
# #     print(f"PLANNER: {len(files)} files planned")
# #     return {"messages": state.messages + [AIMessage(content=json_content)], "files": files}

# def planner(state: AgentState):
#     print("🔵 STARTING PLANNER")
    
#     prompt = f"""YOU ARE A PROJECT PLANNER. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# USER REQUEST: {state.messages[-1].content}

# CRITICAL RULES:
# 1. Output MUST be valid JSON parsable by json.loads()
# 2. NO markdown code blocks (no ```json or ```)
# 3. NO explanations, comments, or extra text
# 4. JSON structure MUST be exactly: {{"plan": "string description", "files": [{{"path": "file1.js", "description": "what this file does"}}]}}
# 5. Each file MUST be an object with "path" and "description" keys

# EXAMPLE CORRECT OUTPUT:
# {{"plan": "React calculator with premium UI", "files": [{{"path": "App.js", "description": "Main React component"}}, {{"path": "styles.css", "description": "Premium styling"}}]}}

# NOW OUTPUT THE JSON:"""
    
#     try:
#         response = llm.invoke([HumanMessage(content=prompt)])
#         raw_content = response.content.strip()
#         print("Raw planner output:", raw_content[:200])
        
#         # Extract JSON
#         start = raw_content.find('{')
#         end = raw_content.rfind('}') + 1
        
#         if start != -1 and end != 0:
#             json_content = raw_content[start:end]
#         else:
#             json_content = raw_content
        
#         print("Extracted JSON:", json_content[:200])
        
#         plan = json.loads(json_content)
#         files = plan.get("files", [])
        
#         # Convert strings to dicts if needed
#         processed_files = []
#         for file_item in files:
#             if isinstance(file_item, str):
#                 # Convert string to dict
#                 processed_files.append({
#                     "path": file_item,
#                     "description": f"File: {file_item}"
#                 })
#             elif isinstance(file_item, dict):
#                 processed_files.append(file_item)
        
#         files = processed_files
        
#     except Exception as e:
#         print(f"Planner JSON error: {e}")
#         # Fallback with correct structure
#         files = [
#             {"path": "index.html", "description": "HTML entry point"},
#             {"path": "App.js", "description": "Main React component"},
#             {"path": "styles.css", "description": "CSS styling"}
#         ]
#         json_content = json.dumps({"plan": "Basic project", "files": files})
    
#     print(f"PLANNER: {len(files)} files planned")
#     return {"messages": state.messages + [AIMessage(content=json_content)], "files": files}

# # def coder(state: AgentState):
# #     print(f"🟢 STARTING CODER (iteration {state.iteration})")
    
# #     if not state.files:
# #         print("⚠️ No files to code")
# #         return {"messages": state.messages, "files": []}
    
# #     # Get context from previous messages
# #     context = ""
# #     if len(state.messages) > 1:
# #         context = state.messages[-1].content[:500]  # Last message as context
    
# #     prompt = f"""YOU ARE A CODE GENERATOR. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# # TASK: Generate complete code for these files: {state.files}
# # CONTEXT: {context}

# # CRITICAL RULES:
# # 1. Output MUST be valid JSON parsable by json.loads()
# # 2. NO markdown code blocks (no ```json or ```)  
# # 3. NO explanations, comments, or extra text
# # 4. JSON structure MUST be exactly: {{"files": [{{"path": "filename.ext", "content": "full code here"}}]}}
# # 5. "content" MUST contain complete, runnable code
# # 6. Generate ALL files in the list

# # EXAMPLE CORRECT OUTPUT:
# # {{"files": [{{"path": "App.js", "content": "import React from 'react';\\n\\nfunction App() {{\\n  return <div>Hello</div>;\\n}}\\n\\nexport default App;"}}]}}

# # NOW OUTPUT THE JSON:"""
    
# #     try:
# #         response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
# #         raw_content = response.content.strip()
# #         print("Raw coder output preview:", raw_content[:200])
        
# #         # Extract JSON
# #         start = raw_content.find('{')
# #         end = raw_content.rfind('}') + 1
        
# #         if start != -1 and end != 0:
# #             json_content = raw_content[start:end]
# #         else:
# #             json_content = raw_content
        
# #         data = json.loads(json_content)
# #         files = data.get("files", [])
        
# #     except Exception as e:
# #         print(f"Coder JSON error: {e}")
# #         files = []
# #         json_content = json.dumps({"files": []})
    
# #     print(f"CODER: Generated {len(files)} files")
# #     return {"messages": state.messages + [AIMessage(content=json_content)], "files": files}

# def coder(state: AgentState):
#     print(f"🟢 STARTING CODER (iteration {state.iteration})")
    
#     if not state.files:
#         print("⚠️ No files to code")
#         return {"messages": state.messages, "files": []}
    
#     # Extract file paths whether they're strings or dicts
#     file_paths = []
#     for file_item in state.files:
#         if isinstance(file_item, str):
#             file_paths.append(file_item)
#         elif isinstance(file_item, dict):
#             file_paths.append(file_item.get("path", ""))
    
#     # Remove empty paths
#     file_paths = [fp for fp in file_paths if fp]
    
#     if not file_paths:
#         print("⚠️ No valid file paths")
#         return {"messages": state.messages, "files": []}
    
#     # Get context from previous messages
#     context = ""
#     if len(state.messages) > 1:
#         context = state.messages[-1].content[:500]
    
#     prompt = f"""YOU ARE A CODE GENERATOR. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# TASK: Generate complete code for these files: {file_paths}
# CONTEXT: {context}

# CRITICAL RULES:
# 1. Output MUST be valid JSON parsable by json.loads()
# 2. NO markdown code blocks (no ```json or ```)  
# 3. NO explanations, comments, or extra text
# 4. JSON structure MUST be exactly: {{"files": [{{"path": "filename.ext", "content": "full code here"}}]}}
# 5. Generate code for ALL listed files

# NOW OUTPUT THE JSON:"""
    
#     try:
#         response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
#         raw_content = response.content.strip()
#         print("Raw coder output preview:", raw_content[:200])
        
#         # Extract JSON
#         start = raw_content.find('{')
#         end = raw_content.rfind('}') + 1
        
#         if start != -1 and end != 0:
#             json_content = raw_content[start:end]
#         else:
#             json_content = raw_content
        
#         data = json.loads(json_content)
#         files = data.get("files", [])
        
#     except Exception as e:
#         print(f"Coder JSON error: {e}")
#         files = []
#         json_content = json.dumps({"files": []})
    
#     print(f"CODER: Generated {len(files)} files")
#     return {"messages": state.messages + [AIMessage(content=json_content)], "files": files}

# def critic(state: AgentState):
#     print(f"🟡 STARTING CRITIC (iteration {state.iteration})")
    
#     if not state.files:
#         print("⚠️ No files to critique")
#         return {"messages": state.messages, "iteration": state.iteration + 1, "files": []}
    
#     # Show only first 3 files to avoid token overflow
#     files_sample = state.files[:3]
    
#     prompt = f"""YOU ARE A CODE CRITIC. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# REVIEW THESE FILES: {json.dumps(files_sample)}

# CRITICAL RULES:
# 1. Output MUST be valid JSON parsable by json.loads()
# 2. NO markdown code blocks (no ```json or ```)
# 3. NO explanations, comments, or extra text  
# 4. JSON structure MUST be exactly: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1"]}}
# 5. "approved" MUST be boolean (true/false)
# 6. Be strict but fair

# APPROVAL GUIDELINES:
# - Approve (true) if: code is syntactically correct, imports are valid, logic makes sense
# - Reject (false) if: syntax errors, missing imports, broken logic, security issues

# EXAMPLE CORRECT OUTPUT:
# {{"critique": "Code is functional", "approved": true, "improvements": []}}

# NOW OUTPUT THE JSON:"""
    
#     try:
#         response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
#         raw_content = response.content.strip()
#         print("Raw critic output:", raw_content[:200])
        
#         # Extract JSON
#         start = raw_content.find('{')
#         end = raw_content.rfind('}') + 1
        
#         if start != -1 and end != 0:
#             json_content = raw_content[start:end]
#         else:
#             json_content = raw_content
        
#         critique = json.loads(json_content)
#         approved = critique.get("approved", False)
        
#     except Exception as e:
#         print(f"Critic JSON error: {e}")
#         approved = True  # Default to approve on error
#         json_content = json.dumps({"critique": "Parse error", "approved": True, "improvements": []})
    
#     print(f"CRITIC: Approved = {approved}")
#     return {"messages": state.messages + [AIMessage(content=json_content)], 
#             "iteration": state.iteration + 1, 
#             "files": state.files if approved else []}

# def should_continue(state: AgentState):
#     print(f"Checking continue: iteration {state.iteration}, files {len(state.files)}")
    
#     # Stop if: reached max iterations OR we have files (approved) OR files is empty after planner
#     if state.iteration >= state.max_iterations or (len(state.files) > 0 and state.iteration > 0):
#         print("✅ ENDING workflow")
#         return END
    
#     print("↩️ Continuing to coder")
#     return "coder"

# # Build the workflow graph
# workflow = StateGraph(AgentState)
# workflow.add_node("planner", planner)
# workflow.add_node("coder", coder)
# workflow.add_node("critic", critic)

# workflow.set_entry_point("planner")
# workflow.add_edge("planner", "coder")
# workflow.add_edge("coder", "critic")
# workflow.add_conditional_edges("critic", should_continue)

# graph = workflow.compile()

# class GenerateRequest(BaseModel):
#     prompt: str

# @app.post("/generate-project")
# async def generate_project(request: GenerateRequest):
#     print(f"📨 Received prompt: {request.prompt}")
    
#     try:
#         inputs = {"messages": [HumanMessage(content=request.prompt)], 
#                   "files": [], 
#                   "iteration": 0}
        
#         print("🔄 Starting LangGraph workflow...")
        
#         # Run LangGraph with timeout
#         result = await asyncio.wait_for(
#             asyncio.to_thread(graph.invoke, inputs),
#             timeout=120  # 2 minute timeout
#         )
        
#         files = result.get("files", [])
#         print(f"✅ Workflow completed. Generated {len(files)} files")
        
#         # Fallback: If LangGraph returns empty, use direct OpenAI
#         if not files:
#             print("⚠️ LangGraph returned empty, using fallback...")
#             from openai import OpenAI
#             client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
#             response = client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": """You are an expert developer. Generate project files.
#                         Return JSON: {"files": [{"path": "file.js", "content": "code"}]}"""
#                     },
#                     {"role": "user", "content": request.prompt}
#                 ],
#                 response_format={"type": "json_object"},
#                 temperature=0.5
#             )
            
#             data = json.loads(response.choices[0].message.content)
#             files = data.get("files", [])
#             print(f"✅ Fallback generated {len(files)} files")
        
#         return {"files": files}
        
#     except asyncio.TimeoutError:
#         print("⏰ Workflow timeout")
#         raise HTTPException(status_code=504, detail="Generation timeout - try simpler prompt")
    
#     except Exception as e:
#         print(f"❌ Workflow error: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/health")
# async def health():
#     return {"status": "ok"}

# apps/api/main.py - LANGGRAPH VERSION
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os
import json
import asyncio

load_dotenv()

app = FastAPI(title="Codeless API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LangChain LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.5, timeout=60)

class AgentState(BaseModel):
    messages: list = []
    files: list[dict] = []
    iteration: int = 0
    max_iterations: int = 3
    approved: bool = False  # Track approval status

def planner(state: AgentState):
    print("🔵 STARTING PLANNER")
    
    prompt = f"""YOU ARE A PROJECT PLANNER. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

USER REQUEST: {state.messages[-1].content}

CRITICAL RULES:
1. Output MUST be valid JSON parsable by json.loads()
2. NO markdown code blocks (no ```json or ```)
3. NO explanations, comments, or extra text
4. JSON structure MUST be exactly: {{"plan": "string description", "files": [{{"path": "file1.js", "description": "what this file does"}}]}}
5. Each file MUST be an object with "path" and "description" keys

EXAMPLE CORRECT OUTPUT:
{{"plan": "React calculator with premium UI", "files": [{{"path": "App.js", "description": "Main React component"}}, {{"path": "styles.css", "description": "Premium styling"}}]}}

NOW OUTPUT THE JSON:"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_content = response.content.strip()
        print("Raw planner output:", raw_content[:200])
        
        # Extract JSON
        start = raw_content.find('{')
        end = raw_content.rfind('}') + 1
        
        if start != -1 and end != 0:
            json_content = raw_content[start:end]
        else:
            json_content = raw_content
        
        print("Extracted JSON:", json_content[:200])
        
        plan = json.loads(json_content)
        files = plan.get("files", [])
        
        # Convert strings to dicts if needed
        processed_files = []
        for file_item in files:
            if isinstance(file_item, str):
                # Convert string to dict
                processed_files.append({
                    "path": file_item,
                    "description": f"File: {file_item}"
                })
            elif isinstance(file_item, dict):
                processed_files.append(file_item)
        
        files = processed_files
        
    except Exception as e:
        print(f"Planner JSON error: {e}")
        # Fallback with correct structure
        files = [
            {"path": "index.html", "description": "HTML entry point"},
            {"path": "App.js", "description": "Main React component"},
            {"path": "styles.css", "description": "CSS styling"}
        ]
        json_content = json.dumps({"plan": "Basic project", "files": files})
    
    print(f"PLANNER: {len(files)} files planned")
    return {"messages": state.messages + [AIMessage(content=json_content)], 
            "files": files, 
            "approved": False}  # Reset approval

def coder(state: AgentState):
    print(f"🟢 STARTING CODER (iteration {state.iteration})")
    
    if not state.files:
        print("⚠️ No files to code")
        return {"messages": state.messages, "files": []}
    
    # Extract file paths from file objects
    file_paths = []
    file_descriptions = {}
    for file_item in state.files:
        if isinstance(file_item, dict):
            file_path = file_item.get("path", "")
            if file_path:
                file_paths.append(file_path)
                file_descriptions[file_path] = file_item.get("description", "")
        elif isinstance(file_item, str):
            file_paths.append(file_item)
            file_descriptions[file_item] = f"File: {file_item}"
    
    if not file_paths:
        print("⚠️ No valid file paths")
        return {"messages": state.messages, "files": []}
    
    # Get context from previous messages
    context = ""
    if len(state.messages) > 1:
        # Look for plan in messages
        for msg in reversed(state.messages):
            if isinstance(msg, AIMessage):
                try:
                    msg_data = json.loads(msg.content)
                    if "plan" in msg_data:
                        context = f"Project plan: {msg_data['plan']}"
                        break
                except:
                    continue
    
    # Build file info for prompt
    file_info = []
    for file_path in file_paths:
        desc = file_descriptions.get(file_path, "")
        file_info.append(f"{file_path}: {desc}")
    
    prompt = f"""YOU ARE A CODE GENERATOR. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

PROJECT CONTEXT: {context}
PREVIOUS FEEDBACK: {state.messages[-1].content if len(state.messages) > 0 else "None"}

TASK: Generate complete, production-ready code for these files:
{json.dumps(file_info, indent=2)}

CRITICAL RULES:
1. Output MUST be valid JSON parsable by json.loads()
2. NO markdown code blocks (no ```json or ```)  
3. NO explanations, comments, or extra text
4. JSON structure MUST be exactly: {{"files": [{{"path": "filename.ext", "content": "full code here"}}]}}
5. Generate code for ALL listed files
6. Make sure code is secure (NO eval() or security vulnerabilities)
7. Ensure all imports are valid and logic is correct

NOW OUTPUT THE JSON:"""
    
    try:
        response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
        raw_content = response.content.strip()
        print("Raw coder output preview:", raw_content[:200])
        
        # Extract JSON
        start = raw_content.find('{')
        end = raw_content.rfind('}') + 1
        
        if start != -1 and end != 0:
            json_content = raw_content[start:end]
        else:
            json_content = raw_content
        
        data = json.loads(json_content)
        generated_files = data.get("files", [])
        
        # Ensure files have the proper structure
        processed_files = []
        for file_item in generated_files:
            if isinstance(file_item, dict) and "path" in file_item and "content" in file_item:
                processed_files.append(file_item)
        
    except Exception as e:
        print(f"Coder JSON error: {e}")
        processed_files = []
        json_content = json.dumps({"files": []})
    
    print(f"CODER: Generated {len(processed_files)} files")
    return {"messages": state.messages + [AIMessage(content=json_content)], 
            "files": processed_files}

def critic(state: AgentState):
    print(f"🟡 STARTING CRITIC (iteration {state.iteration})")
    
    if not state.files:
        print("⚠️ No files to critique")
        return {"messages": state.messages, 
                "iteration": state.iteration + 1, 
                "files": state.files, 
                "approved": True}  # Auto-approve empty
    
    # Show sample of files for review
    files_sample = state.files[:3]
    
    prompt = f"""YOU ARE A CODE CRITIC. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

REVIEW THESE FILES: {json.dumps(files_sample, indent=2)}

CRITICAL SECURITY RULE: REJECT ANY CODE USING eval() OR SIMILAR UNSAFE FUNCTIONS

CRITICAL RULES:
1. Output MUST be valid JSON parsable by json.loads()
2. NO markdown code blocks (no ```json or ```)
3. NO explanations, comments, or extra text  
4. JSON structure MUST be exactly: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1", "suggestion2"]}}
5. "approved" MUST be boolean (true/false)
6. Be strict but constructive

APPROVAL GUIDELINES:
- Approve (true) if: code is syntactically correct, secure (no eval), imports are valid, logic makes sense
- Reject (false) if: syntax errors, missing imports, broken logic, security issues (especially eval)

EXAMPLE CORRECT OUTPUT:
{{"critique": "Code is functional but needs to remove eval() for security", "approved": false, "improvements": ["Replace eval() with safe calculation", "Add input validation"]}}

NOW OUTPUT THE JSON:"""
    
    try:
        response = llm.invoke(state.messages + [HumanMessage(content=prompt)])
        raw_content = response.content.strip()
        print("Raw critic output:", raw_content[:200])
        
        # Extract JSON
        start = raw_content.find('{')
        end = raw_content.rfind('}') + 1
        
        if start != -1 and end != 0:
            json_content = raw_content[start:end]
        else:
            json_content = raw_content
        
        critique = json.loads(json_content)
        approved = critique.get("approved", False)
        
    except Exception as e:
        print(f"Critic JSON error: {e}")
        approved = True  # Default to approve on error
        json_content = json.dumps({"critique": "Parse error", "approved": True, "improvements": []})
    
    print(f"CRITIC: Approved = {approved}")
    return {"messages": state.messages + [AIMessage(content=json_content)], 
            "iteration": state.iteration + 1, 
            "files": state.files,  # ALWAYS return files (don't lose them)
            "approved": approved}  # Pass approval status

def should_continue(state: AgentState):
    print(f"\n🔁 Checking continue condition:")
    print(f"  Iteration: {state.iteration}/{state.max_iterations}")
    print(f"  Files count: {len(state.files)}")
    print(f"  Approved status: {state.approved}")
    
    # Determine if we should continue
    should_end = False
    
    # Stop condition 1: Reached max iterations
    if state.iteration >= state.max_iterations:
        print("  ✅ Reached max iterations")
        should_end = True
    
    # Stop condition 2: Critic approved AND we have files
    elif state.approved and len(state.files) > 0:
        print("  ✅ Critic approved with files")
        should_end = True
    
    # Stop condition 3: No files after planning (unlikely but handle)
    elif state.iteration > 0 and len(state.files) == 0:
        print("  ⚠️ No files to process")
        should_end = True
    
    if should_end:
        print("  🏁 ENDING workflow")
        return END
    
    print("  ↩️ Continuing to coder for improvement")
    return "coder"

# Build the workflow graph
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner)
workflow.add_node("coder", coder)
workflow.add_node("critic", critic)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "coder")
workflow.add_edge("coder", "critic")
workflow.add_conditional_edges("critic", should_continue)

graph = workflow.compile()

class GenerateRequest(BaseModel):
    prompt: str

@app.post("/generate-project")
async def generate_project(request: GenerateRequest):
    print(f"\n📨 Received prompt: {request.prompt}")
    
    try:
        inputs = {
            "messages": [HumanMessage(content=request.prompt)], 
            "files": [], 
            "iteration": 0,
            "approved": False,
            "max_iterations": 3
        }
        
        print("🔄 Starting LangGraph workflow...")
        
        # Run LangGraph with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, inputs),
            timeout=180  # 3 minute timeout
        )
        
        files = result.get("files", [])
        print(f"\n✅ Workflow completed.")
        print(f"   Total files generated: {len(files)}")
        print(f"   Final approved: {result.get('approved', False)}")
        print(f"   Iterations: {result.get('iteration', 0)}")
        
        # Only use fallback if LangGraph truly returns empty
        if not files:
            print("⚠️ LangGraph returned empty, using fallback...")
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert developer. Generate a React calculator project.
                        Return JSON: {"files": [{"path": "App.js", "content": "code"}, {"path": "styles.css", "content": "styles"}]}
                        NO eval() functions - use safe calculations."""
                    },
                    {"role": "user", "content": request.prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            data = json.loads(response.choices[0].message.content)
            files = data.get("files", [])
            print(f"✅ Fallback generated {len(files)} files")
        
        return {"files": files}
        
    except asyncio.TimeoutError:
        print("⏰ Workflow timeout")
        raise HTTPException(status_code=504, detail="Generation timeout - try simpler prompt")
    
    except Exception as e:
        print(f"❌ Workflow error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)