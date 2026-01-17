
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph, END
# from langchain_core.messages import HumanMessage, AIMessage
# from dotenv import load_dotenv
# from llama_index.core import VectorStoreIndex
# from llama_index.vector_stores.postgres import PGVectorStore
# from llama_index.embeddings.openai import OpenAIEmbedding
# from supabase import create_client
# import os
# import json
# import asyncio

# load_dotenv()
# # After load_dotenv()
# supabase_url = os.getenv("SUPABASE_URL")
# service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# if not supabase_url or not service_role_key:
#   raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")

# project_ref = supabase_url.replace("https://", "").split(".")[0]

# # Direct connection with service_role (port 5432)
# vector_store = PGVectorStore.from_params(
#   database="postgres",
#   host=f"db.{project_ref}.supabase.co",
#   port=5432,
#   user="postgres",
#   password=service_role_key,
#   table_name="projects",
#   embed_dim=1536,
# )
# index = VectorStoreIndex.from_vector_store(vector_store)

# # Supabase client for REST insert (service_role)
# supabase = create_client(supabase_url, service_role_key)

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
#     approved: bool = False  # Track approval status

# def planner(state: AgentState):
#     print("🔵 STARTING PLANNER with RAG (REST)")
    
#     # Retrieve similar projects via REST (simple text search on prompt)
#     try:
#         response = supabase.table("projects").select("*").ilike("prompt", f"%{state.messages[-1].content[:50]}%").limit(3).execute()
#         context = ""
#         for row in response.data:
#             context += f"Previous project prompt: {row['prompt']}\nFiles: {json.dumps(row['files'][:2])}\n\n"  # Sample
#     except Exception as e:
#         print("RAG retrieve error:", str(e))
#         context = "No previous projects found."
    
#     prompt = f"""{context}
    
#     USER REQUEST: {state.messages[-1].content}
    
#     Plan the project. Output ONLY JSON: {{"plan": "description", "files": ["path1.js", ...]}}"""
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
#     return {"messages": state.messages + [AIMessage(content=json_content)], 
#             "files": files, 
#             "approved": False}  # Reset approval

# def coder(state: AgentState):
#     print(f"🟢 STARTING CODER (iteration {state.iteration})")
    
#     if not state.files:
#         print("⚠️ No files to code")
#         return {"messages": state.messages, "files": []}
    
#     # Extract file paths from file objects
#     file_paths = []
#     file_descriptions = {}
#     for file_item in state.files:
#         if isinstance(file_item, dict):
#             file_path = file_item.get("path", "")
#             if file_path:
#                 file_paths.append(file_path)
#                 file_descriptions[file_path] = file_item.get("description", "")
#         elif isinstance(file_item, str):
#             file_paths.append(file_item)
#             file_descriptions[file_item] = f"File: {file_item}"
    
#     if not file_paths:
#         print("⚠️ No valid file paths")
#         return {"messages": state.messages, "files": []}
    
#     # Get context from previous messages
#     context = ""
#     if len(state.messages) > 1:
#         # Look for plan in messages
#         for msg in reversed(state.messages):
#             if isinstance(msg, AIMessage):
#                 try:
#                     msg_data = json.loads(msg.content)
#                     if "plan" in msg_data:
#                         context = f"Project plan: {msg_data['plan']}"
#                         break
#                 except:
#                     continue
    
#     # Build file info for prompt
#     file_info = []
#     for file_path in file_paths:
#         desc = file_descriptions.get(file_path, "")
#         file_info.append(f"{file_path}: {desc}")
    
#     prompt = f"""YOU ARE A CODE GENERATOR. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# PROJECT CONTEXT: {context}
# PREVIOUS FEEDBACK: {state.messages[-1].content if len(state.messages) > 0 else "None"}

# TASK: Generate complete, production-ready code for these files:
# {json.dumps(file_info, indent=2)}

# CRITICAL RULES:
# 1. Output MUST be valid JSON parsable by json.loads()
# 2. NO markdown code blocks (no ```json or ```)  
# 3. NO explanations, comments, or extra text
# 4. JSON structure MUST be exactly: {{"files": [{{"path": "filename.ext", "content": "full code here"}}]}}
# 5. Generate code for ALL listed files
# 6. Make sure code is secure (NO eval() or security vulnerabilities)
# 7. Ensure all imports are valid and logic is correct

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
#         generated_files = data.get("files", [])
        
#         # Ensure files have the proper structure
#         processed_files = []
#         for file_item in generated_files:
#             if isinstance(file_item, dict) and "path" in file_item and "content" in file_item:
#                 processed_files.append(file_item)
        
#     except Exception as e:
#         print(f"Coder JSON error: {e}")
#         processed_files = []
#         json_content = json.dumps({"files": []})
    
#     print(f"CODER: Generated {len(processed_files)} files")
#     return {"messages": state.messages + [AIMessage(content=json_content)], 
#             "files": processed_files}

# def critic(state: AgentState):
#     print(f"🟡 STARTING CRITIC (iteration {state.iteration})")
    
#     if not state.files:
#         print("⚠️ No files to critique")
#         return {"messages": state.messages, 
#                 "iteration": state.iteration + 1, 
#                 "files": state.files, 
#                 "approved": True}  # Auto-approve empty
    
#     # Show sample of files for review
#     files_sample = state.files[:3]
    
#     prompt = f"""YOU ARE A CODE CRITIC. YOU MUST OUTPUT ONLY PURE JSON, NOTHING ELSE.

# REVIEW THESE FILES: {json.dumps(files_sample, indent=2)}

# CRITICAL SECURITY RULE: REJECT ANY CODE USING eval() OR SIMILAR UNSAFE FUNCTIONS

# CRITICAL RULES:
# 1. Output MUST be valid JSON parsable by json.loads()
# 2. NO markdown code blocks (no ```json or ```)
# 3. NO explanations, comments, or extra text  
# 4. JSON structure MUST be exactly: {{"critique": "brief feedback", "approved": true/false, "improvements": ["suggestion1", "suggestion2"]}}
# 5. "approved" MUST be boolean (true/false)
# 6. Be strict but constructive

# APPROVAL GUIDELINES:
# - Approve (true) if: code is syntactically correct, secure (no eval), imports are valid, logic makes sense
# - Reject (false) if: syntax errors, missing imports, broken logic, security issues (especially eval)

# EXAMPLE CORRECT OUTPUT:
# {{"critique": "Code is functional but needs to remove eval() for security", "approved": false, "improvements": ["Replace eval() with safe calculation", "Add input validation"]}}

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
#             "files": state.files,  # ALWAYS return files (don't lose them)
#             "approved": approved}  # Pass approval status

# def should_continue(state: AgentState):
#     print(f"\n🔁 Checking continue condition:")
#     print(f"  Iteration: {state.iteration}/{state.max_iterations}")
#     print(f"  Files count: {len(state.files)}")
#     print(f"  Approved status: {state.approved}")
    
#     # Determine if we should continue
#     should_end = False
    
#     # Stop condition 1: Reached max iterations
#     if state.iteration >= state.max_iterations:
#         print("  ✅ Reached max iterations")
#         should_end = True
    
#     # Stop condition 2: Critic approved AND we have files
#     elif state.approved and len(state.files) > 0:
#         print("  ✅ Critic approved with files")
#         should_end = True
    
#     # Stop condition 3: No files after planning (unlikely but handle)
#     elif state.iteration > 0 and len(state.files) == 0:
#         print("  ⚠️ No files to process")
#         should_end = True
    
#     if should_end:
#         print("  🏁 ENDING workflow")
#         return END
    
#     print("  ↩️ Continuing to coder for improvement")
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
#   print(f"\n📨 Received prompt: {request.prompt}")
  
#   try:
#     inputs = {
#       "messages": [HumanMessage(content=request.prompt)], 
#       "files": [], 
#       "iteration": 0,
#       "approved": False,
#       "max_iterations": 3
#     }
    
#     print("🔄 Starting LangGraph workflow...")
    
#     result = await asyncio.wait_for(
#       asyncio.to_thread(graph.invoke, inputs),
#       timeout=180
#     )

#     files = result.get("files", [])
#     print(f"\n✅ Workflow completed. {len(files)} files generated.")

#     # Save to Supabase with embedding
#     embed_model = OpenAIEmbedding()
#     project_text = request.prompt + " " + json.dumps(files)
#     embedding = embed_model.get_text_embedding(project_text)
#     try:
#         supabase.table("projects").insert({
#             "user_id": "temp-user",
#             "prompt": request.prompt,
#             "files": result["files"],
#         }).execute()
#         print("Saved project to Supabase (REST)")
#     except Exception as e:
#         print("Save error:", str(e))

#     return {"files": files}
    
#   except asyncio.TimeoutError:
#     print("⏰ Workflow timeout")
#     raise HTTPException(status_code=504, detail="Generation timeout")
#   except Exception as e:
#     print(f"❌ Error: {str(e)}")
#     raise HTTPException(status_code=500, detail=str(e))

# @app.get("/health")
# async def health():
#   return {"status": "ok"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)



# apps/api/main.py - LANGGRAPH VERSION (Phase 9 complete, Phase 10 REST save only - no pgvector connection)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from supabase import create_client
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

# Supabase client for REST save (service_role key for write)
supabase_url = os.getenv("SUPABASE_URL")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not service_role_key:
  raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required in .env")

supabase = create_client(supabase_url, service_role_key)

class AgentState(BaseModel):
    messages: list = []
    files: list[dict] = []
    iteration: int = 0
    max_iterations: int = 3
    approved: bool = False  # Track approval status

def planner(state: AgentState):
    print("🔵 STARTING PLANNER with RAG (REST retrieve)")
    
    # Retrieve similar previous projects (simple prompt search)
    try:
        response = supabase.table("projects").select("prompt, files").ilike("prompt", f"%{state.messages[-1].content[:30]}%").limit(3).execute()
        context = "Previous similar projects found:\n"
        for row in response.data:
            context += f"- Prompt: {row['prompt']}\n  Files: {list(f['path'] for f in row['files'][:3])}\n"
    except Exception as e:
        print("RAG retrieve error:", str(e))
        context = "No previous projects found."
    
    print("RAG context:", context)
    
    prompt = f"""{context}
    
    USER REQUEST: {state.messages[-1].content}
    
    Plan the project (improve previous if relevant). Output ONLY JSON: {{"plan": "description", "files": ["path1.js", ...]}}"""
    
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
                processed_files.append({
                    "path": file_item,
                    "description": f"File: {file_item}"
                })
            elif isinstance(file_item, dict):
                processed_files.append(file_item)
        
        files = processed_files
        
    except Exception as e:
        print(f"Planner JSON error: {e}")
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

    should_end = False
    
    if state.iteration >= state.max_iterations:
        print("  ✅ Reached max iterations")
        should_end = True
    
    elif state.approved and len(state.files) > 0:
        print("  ✅ Critic approved with files")
        should_end = True
    
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
        
        result = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, inputs),
            timeout=180  # 3 minute timeout
        )

        files = result.get("files", [])
        print(f"\n✅ Workflow completed.")
        print(f"   Total files generated: {len(files)}")
        print(f"   Final approved: {result.get('approved', False)}")
        print(f"   Iterations: {result.get('iteration', 0)}")
        
        # Save project to Supabase (REST)
        # Save project to Supabase (REST)
        try:
            supabase.table("projects").insert({ 
                "user_id": None,  # or "temp-user" (now text/null allowed)
                "prompt": request.prompt,
                "files": result["files"]
            }).execute()
            print("Saved project to Supabase")
        except Exception as e:
            print("Save error:", str(e))
        
        # Fallback if empty
        if not files:
            print("⚠️ LangGraph returned empty, using fallback...")
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Generate a complete project as JSON: {\"files\": [{\"path\": \"file.js\", \"content\": \"code\"}]}"},
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