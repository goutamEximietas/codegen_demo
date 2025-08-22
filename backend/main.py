# main.py
#
# This script implements an enhanced AutoGen-powered autonomous agent system,
# fully compatible with the latest versions of AutoGen (v0.10.0+).
# It now loads LLM configuration from the OAI_CONFIG_LIST file and
# uses the correct import paths for the latest autogen-agentchat library.

import os
import json
from typing import Dict, List, Any
import argparse
import subprocess
import time
from functools import partial
import asyncio
import inspect as _inspect
import docx
import threading
import httpx


# FastAPI for API endpoint
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,RedirectResponse
import uvicorn

# AutoGen v0.7.x APIs
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ChatCompletionClient, ModelInfo, ModelCapabilities
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.models.openai.config import AzureOpenAIClientConfiguration
from typing import Dict, List, Any
import aiofiles
from fastapi import HTTPException
# Import the dashboard functionality
from dashboard import start_dashboard_server_in_thread

GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", None)
# "http://localhost:5001/api"
NODEJS_BACKEND_BASE_URL = os.getenv("NODEJS_BACKEND_BASE_URL", None)
print(f"Using GitHub repository URL: {GITHUB_REPO_URL}")

# Global socketio instance for emitting events
socketio = None

# --- NEW: Global state for the hybrid progress system ---
_approved_plan: Dict[str, Any] | None = None
_completed_task_ids: set[str] = set()
# ----------------------------------------------------------------------------
# Event Emitter for Dashboard
# ----------------------------------------------------------------------------

def emit_status(message: str):
    """Sends a general status update to the dashboard."""
    if socketio:
        socketio.emit('status_update', {'message': message})

def emit_agent_message(sender, recipient, message):
    """Sends an agent-to-agent message to the dashboard."""
    if socketio:
        recipient_name = recipient.name if hasattr(recipient, 'name') else str(recipient)
        content = message.get("content", "") if isinstance(message, dict) else message
        
        if not content or content.strip() == "":
            return
        
         # --- NEW LOGIC TO DETECT TASK COMPLETION ---
        # Use regex to find all task completion markers in the message
        completed_tasks = re.findall(r"TASK_COMPLETED: ([\w-]+)", content)
        if completed_tasks:
            for task_id in completed_tasks:
                print(f"DETECTED TASK COMPLETION: {task_id}")
                # Emit a dedicated event for this completed task
                socketio.emit('task_completed_update', {'task_id': task_id})
        # --- END OF NEW LOGIC ---
            
        socketio.emit('agent_message', {
            'sender': sender.name,
            'recipient': recipient_name,
            'message': content
        })

def emit_tool_call(agent_name, tool_name, args):
    """Sends a tool call event to the dashboard."""
    if socketio:
        socketio.emit('tool_call', {
            'agent': agent_name,
            'tool': tool_name,
            'args': args
        })

# --- NEW: Heuristic-based task completion detection ---
def _check_and_emit_task_completion(action_description: str):
    """
    Checks if an action (like creating a file) completes a task from the plan.
    This is the implicit, heuristic-based part of our hybrid system.
    """
    global _approved_plan, _completed_task_ids
    if not _approved_plan:
        return

    action_desc_lower = action_description.lower()
    
    all_tasks = [
        task
        for team in _approved_plan.get("teams", [])
        for role in team.get("roles", [])
        for task in role.get("tasks", [])
    ]

    for task in all_tasks:
        task_id = task.get("task_id")
        if task_id in _completed_task_ids:
            continue

        # Extract keywords from the task description
        description = task.get("description", "").lower()
        keywords = re.findall(r'\b\w{4,}\b', description) # Find words with 4+ letters
        
        # Check if the action description strongly relates to the task
        # A simple but effective heuristic: does the file path contain a key task word?
        if any(keyword in action_desc_lower for keyword in keywords if keyword not in ["using", "with", "file", "code"]):
            print(f" IMPLICITLY DETECTED TASK COMPLETION: {task_id} (Action: {action_description})")
            _completed_task_ids.add(task_id)
            if socketio:
                socketio.emit('task_completed_update', {'task_id': task_id})
            # Once a task is matched, we stop checking for this action
            break

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

def load_config_from_file(file_path: str = "OAI_CONFIG_LIST") -> List[Dict[str, Any]]:
    """Load model configuration list from JSON file (OAI_CONFIG_LIST format)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Configuration file not found: {file_path}. Please provide OAI_CONFIG_LIST."
        )
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def make_model_client(config: Dict[str, Any]) -> ChatCompletionClient:
    """Create an Azure OpenAI client for autogen 0.7.x from a config entry.

    Expected keys (from OAI_CONFIG_LIST):
    - model -> maps to azure_deployment
    - api_key
    - base_url -> maps to azure_endpoint
    - api_version
    Optional: temperature, timeout, etc.
    """
    if config.get("api_type", "").lower() == "azure":
        deployment = config.get("model") or config.get("azure_deployment")
        endpoint = config.get("base_url") or config.get("azure_endpoint")
        # Map to a known OpenAI model name for better token/cost estimation (optional)
        mapped_model = config.get("openai_model")
        if not mapped_model and deployment == "model-router":
            mapped_model = "gpt-4o-mini-2024-07-18"
        return AzureOpenAIChatCompletionClient(
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            model=mapped_model or deployment,
            api_version=config.get("api_version", "2024-02-01"),
            api_key=config.get("api_key"),
            temperature=float(config.get("temperature", 0.1)),
            timeout=float(config.get("timeout", 600)),
            model_info=ModelInfo(
                family="azure-openai",
                function_calling=True,
                json_output=True,
                vision=False,
                structured_output=False,
                multiple_system_messages=False,
            ),
        )
    raise ValueError("Only Azure OpenAI config is supported by this script.")

# Load first usable model client from OAI_CONFIG_LIST
_config_list = load_config_from_file()
MODEL_CLIENT: ChatCompletionClient = make_model_client(_config_list[0])
DEFAULT_TEMPERATURE = float(_config_list[0].get("temperature", 0.1))

# ----------------------------------------------------------------------------
# Async helpers
# ----------------------------------------------------------------------------

def _run_sync(maybe_coro):
    """Run a coroutine to completion if needed, else return the value."""
    if _inspect.iscoroutine(maybe_coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # If we're in an event loop, use asyncio.ensure_future and await
            # But since this is a sync function, use asyncio.run_coroutine_threadsafe
            # or nest_asyncio if you want to allow nested loops
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(maybe_coro)
        else:
            return asyncio.run(maybe_coro)
    return maybe_coro

def agent_run(agent: AssistantAgent, task: str):
    return _run_sync(agent.run(task=task))

def group_run(group: RoundRobinGroupChat, task: str):
    return _run_sync(group.run(task=task))

# ----------------------------------------------------------------------------
# JSON helpers
# ----------------------------------------------------------------------------

import re

def _extract_json_str(text: str) -> str | None:
    """Try to extract a JSON object string from LLM text output.
    Strategies: fenced ```json ... ```, then first balanced {...} block.
    """
    if not isinstance(text, str):
        return None
    # fenced JSON
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fence:
        return fence.group(1)
    # balanced braces
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


# ----------------------------------------------------------------------------
# OS-Aware File Operation Tools (with Monitoring)
# ----------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Reads the content of a file for debugging purposes."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Content of {path}:\n{content}"
    except Exception as e:
        return f"Error reading file {path}: {e}"

def list_files(directory: str = ".") -> str:
    """Lists files in a directory for debugging purposes."""
    try:
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        return f"Files in {directory}:\n" + "\n".join(files) if files else f"No files found in {directory}"
    except Exception as e:
        return f"Error listing files in {directory}: {e}"


def create_directory(path: str) -> str:
    """Creates a directory and emits an event to the dashboard."""
    emit_tool_call("FileSystemTool", "create_directory", {'path': path})
    try:
        os.makedirs(path, exist_ok=True)
        message = f"Successfully created directory: {path}"
        emit_status(f" {message}")
        print(f" {message}")
        _check_and_emit_task_completion(path)
        return message
    except Exception as e:
        error_msg = f"Error creating directory {path}: {e}"
        emit_status(f"{error_msg}")
        print(f"{error_msg}")
        return error_msg

def create_file(path: str, content: str) -> str:
    """Creates a file and emits an event to the dashboard."""
    emit_tool_call("FileSystemTool", "create_file", {'path': path, 'content_length': len(content)})
    try:
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        message = f"Successfully created file: {path} ({len(content)} characters)"
        emit_status(f"{message}")
        print(f"{message}")
        _check_and_emit_task_completion(path)
        return message
    except Exception as e:
        error_msg = f"Error creating file {path}: {e}"
        emit_status(f"{error_msg}")
        print(f"{error_msg}")
        return error_msg

# ----------------------------------------------------------------------------
# GitHub Integration & Utility Functions
# ----------------------------------------------------------------------------

def commit_to_github(repo_url: str, workspace_dir: str, commit_message: str = "Initial commit by AutoGen"):
    """Commits code to GitHub and emits status updates."""
    if not repo_url:
        print("GitHub repository URL not provided. Skipping commit.")
        return
    
    emit_status(f"Committing code to GitHub repository: {repo_url}")
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        subprocess.run(["git", "config", "--global", "user.name", "AutoGen Agent"], cwd=workspace_dir, check=True)
        subprocess.run(["git", "config", "--global", "user.email", "autogen@example.com"], cwd=workspace_dir, check=True)
        subprocess.run(["git", "init"], cwd=workspace_dir, check=True)
        subprocess.run(["git", "add", "."], cwd=workspace_dir, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=workspace_dir, check=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=workspace_dir, check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=workspace_dir, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=workspace_dir, check=True)
        emit_status("Code successfully committed and pushed to GitHub.")
        print("Code successfully committed and pushed to GitHub.")
    except Exception as e:
        error_message = f"An error occurred during GitHub integration: {e}"
        emit_status(error_message)
        print(error_message)

def read_spec_document(file_path: str) -> str:
    """Reads the content of the technical specification document."""
    _, extension = os.path.splitext(file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Specification file not found at: {file_path}")
    content = ""
    try:
        if extension == ".docx":
            doc = docx.Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif extension in [".md", ".txt"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            raise ValueError(f"Unsupported file format: {extension}.")
    except Exception as e:
        raise IOError(f"Error reading spec file: {e}") from e
    return content

# ----------------------------------------------------------------------------
# Core Agent Logic (with Monitoring Hooks)
# ----------------------------------------------------------------------------

def dynamic_planning_and_validation(spec_content: str):
    """Orchestrates the dynamic planning and validation phase with monitoring."""
    emit_status("Starting Dynamic Planning & Validation Phase...")
    
    # --- ADDED global keyword ---
    global _approved_plan

    planner_system_message = """You are a world-class AI software architect with expertise in full-stack development, DevOps, and project management. Your role is to analyze technical specifications and create comprehensive, detailed development plans.

CORE RESPONSIBILITIES:
- Analyze technical specifications thoroughly
- Identify all required teams, roles, and tasks
- Create structured, actionable development plans
- Ensure comprehensive coverage of all requirements
- Output only valid JSON without any explanations

OUTPUT FORMAT:
You must output ONLY valid JSON in this exact structure:
{
  "teams": [
    {
      "name": "TeamName",
      "roles": [
        {
          "role": "RoleName", 
          "tasks": [
            {
              "task_id": "unique_id",
              "description": "detailed task description"
            }
          ]
        }
      ]
    }
  ]
}

PLANNING GUIDELINES:
- Create teams for: Frontend, Backend, Database, QA/Testing, DevOps
- Include managers for each team (e.g., "FrontendManager", "BackendManager")
- Include senior developers (e.g., "SeniorFrontendDeveloper", "SeniorBackendDeveloper")
- Break down complex features into specific, actionable tasks
- Ensure tasks are atomic and clearly defined
- Include setup, development, testing, and documentation tasks
- Consider dependencies between tasks
"""
    
    reviewer_system_message = """You are a meticulous Quality Assurance manager and technical reviewer with extensive experience in software project management and architecture validation.

CORE RESPONSIBILITIES:
- Review development plans against technical specifications
- Validate completeness and accuracy of team structures
- Ensure all requirements are addressed
- Verify task decomposition is appropriate
- Check for missing components or dependencies

REVIEW CRITERIA:
1. All technical requirements from the spec are covered
2. Team structure is appropriate for the project scope
3. Tasks are well-defined and actionable
4. Dependencies are properly identified
5. Testing and quality assurance are included
6. Documentation tasks are present
7. DevOps and deployment considerations are addressed

APPROVAL PROCESS:
- If the plan meets all criteria, include the word "APPROVED" in your response
- If revisions are needed, provide specific, actionable feedback
- Focus on JSON structure compliance and requirement coverage
- Be thorough but constructive in feedback
"""
    
    planner = AssistantAgent(
        name="Planner",
        model_client=MODEL_CLIENT,
        system_message=planner_system_message,
    )
    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=MODEL_CLIENT,
        system_message=reviewer_system_message,
    )
    # Controller agent (optional, used for dashboard messages etc.)
    user_proxy = UserProxyAgent(name="UserProxy")

    approved_plan = None
    last_valid_plan = None
    for i in range(8):
        emit_status(f"--- Planning Iteration {i+1} ---")
        # Ask planner for a JSON plan
        reply = agent_run(planner, task=(
            "You are a senior software planner. Read the spec and output ONLY valid JSON for the plan."
            " Do not include explanations or markdown fences. Keys: teams:[{name, roles:[{role, tasks:[{task_id, description}]}]}]."
            " Ensure well-formed JSON.\n\nSPEC:\n"
            f"{spec_content}"
        ))
        
        # Extract content from the reply - handle different response types
        raw = None
        if hasattr(reply, 'content'):
            raw = reply.content
        elif hasattr(reply, 'messages') and reply.messages:
            # Get the last message from the assistant
            for msg in reversed(reply.messages):
                if hasattr(msg, 'source') and msg.source == 'Planner':
                    raw = msg.content
                    break
        else:
            raw = str(reply)
        
        plan_json_str = raw
        
        if plan_json_str:
            plan_json_str = plan_json_str.strip()
        # Try extraction if not pure JSON
        if plan_json_str and not plan_json_str.startswith('{'):
            maybe = _extract_json_str(plan_json_str)
            if maybe:
                plan_json_str = maybe
        try:
            plan_data = json.loads(plan_json_str)
            last_valid_plan = plan_data
            emit_status("Plan generated successfully.")
        except json.JSONDecodeError:
            emit_status("Planner did not output valid JSON. Retrying with stricter guidance...")
            continue

        review_reply = agent_run(reviewer, task=(
            "You are a meticulous reviewer. Verify the plan against the spec."
            " If acceptable, include the word APPROVED. Otherwise, list concrete JSON-level changes.\n\n"
            f"Spec:\n{spec_content}\n\nPlan:\n{json.dumps(plan_data, indent=2)}"
        ))
        
        # Extract review feedback
        review_feedback = None
        if hasattr(review_reply, 'content'):
            review_feedback = review_reply.content
        elif hasattr(review_reply, 'messages') and review_reply.messages:
            for msg in reversed(review_reply.messages):
                if hasattr(msg, 'source') and msg.source == 'Reviewer':
                    review_feedback = msg.content
                    break
        else:
            review_feedback = str(review_reply)
        if "APPROVED" in review_feedback:
            emit_status("Plan approved by the Reviewer!")
            approved_plan = plan_data
            break
        else:
            emit_status("Plan needs revision. Sending feedback to Planner.")
            _ = agent_run(planner, task=(
                "Revise the plan JSON based on this feedback. Output ONLY valid JSON, no prose.\n\n"
                f"FEEDBACK:\n{review_feedback}\n\nCURRENT PLAN JSON (fix in place):\n{json.dumps(plan_data)}"
            ))
    if not approved_plan:
        if last_valid_plan is not None:
            emit_status("Proceeding with the latest valid plan (no explicit approval).")
            approved_plan = last_valid_plan
        else:
            raise Exception("Failed to get an approved plan after several iterations.")
    
     # --- ADDED line to set the global plan ---
    _approved_plan = approved_plan # This makes the plan accessible to our heuristic checker
    
    emit_status("Final Approved Plan:")
    if socketio:
        socketio.emit('final_plan_update', approved_plan)
    print("\nFINAL APPROVED PLAN:")
    print(json.dumps(approved_plan, indent=2))
    emit_status(f"Plan contains {len(approved_plan.get('teams', []))} teams")
    
    return approved_plan



def execute_development_plan(plan: Dict[str, Any]):
    """Executes the development plan using the modern tool usage pattern."""
    emit_status("\nStarting Development Execution Phase...")
    workspace_dir = "autogen_workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    emit_status(f"Project workspace created at: ./{workspace_dir}")

    # Change to workspace directory for file operations
    original_cwd = os.getcwd()
    os.chdir(workspace_dir)

    try:
        project_manager = UserProxyAgent(
            name="ProjectManager",
            description="A project manager that coordinates team execution",
            input_func=lambda prompt: "proceed"  # Always respond with proceed for autonomous operation
        )
        
        all_agents = {"ProjectManager": project_manager}
        for team_data in plan.get("teams", []):
            for role_data in team_data.get("roles", []):
                role_name = role_data["role"]
                if role_name not in all_agents:
                    is_manager = "Manager" in role_name
                    
                    if is_manager:
                        system_message = f"""You are the {role_name} responsible for leading your team and ensuring project success.

CORE RESPONSIBILITIES:
- Lead and coordinate your team members
- Assign specific tasks to team members based on the project plan
- Review and validate all deliverables from your team
- Ensure code quality, testing, and documentation standards
- Coordinate with other team managers as needed
- Report progress and completion status

MANAGEMENT GUIDELINES:
- Break down complex tasks into smaller, manageable pieces
- Provide clear, specific instructions to team members
- Review all code and deliverables before approving
- Ensure proper testing and documentation
- Maintain project standards and best practices

Always start by analyzing the tasks assigned to your team and creating a detailed execution plan."""
                    else:
                        system_message = f"""You are an expert {role_name} with deep technical expertise and practical experience.

CORE RESPONSIBILITIES:
- Execute assigned tasks with precision and quality
- Use provided tools for all file and directory operations
- Write clean, efficient, and well-documented code
- Follow industry best practices and coding standards
- Create comprehensive unit tests for all code
- Document your work thoroughly
- Report progress and completion to your Team Manager

TECHNICAL GUIDELINES:
- Always use the create_directory and create_file tools for file operations
- Write production-ready code with proper error handling
- Include comprehensive comments and documentation
- Create unit tests for all functions and components
- Follow the specific technology stack requirements
- Ensure code is secure and follows best practices

IMPORTANT: You must use the provided tools (create_directory, create_file) for all file operations. Do not just describe what you would do - actually create the files using the tools.

***CRITICAL INSTRUCTION***
When you have successfully completed a task, you MUST report it by including the following string on a new line in your response:
TASK_COMPLETED: [task_id]

For example, if you just finished task 'FE-SDEV-001', you must include this exact line:
TASK_COMPLETED: FE-SDEV-001

This is the only way your work will be tracked. Do not forget this step.
"""

                    agent_tools = []
                    if not is_manager:
                        # In v0.7.x tools can be passed as callables; they will be wrapped
                        agent_tools = [create_directory, create_file, list_files, read_file]

                    agent = AssistantAgent(
                        name=role_name,
                        model_client=MODEL_CLIENT,
                        system_message=system_message,
                        tools=agent_tools or None,
                    )
                    all_agents[role_name] = agent

        # Execute each team sequentially with enhanced coordination
        for team_data in plan.get("teams", []):
            team_name = team_data["name"]
            emit_status(f"\n--- Activating Team: {team_name} ---")
            
            team_agents = [all_agents[role["role"]] for role in team_data["roles"]]
            team_agents.append(project_manager)

            # Build a RoundRobin group and run with detailed task instructions
            group = RoundRobinGroupChat(participants=team_agents, max_turns=100)
            
            # Create detailed task breakdown for the team
            all_tasks_for_team = []
            for role in team_data["roles"]:
                role_name = role["role"]
                for task in role["tasks"]:
                    all_tasks_for_team.append({
                        "role": role_name,
                        "task_id": task["task_id"],
                        "description": task["description"]
                    })

            # Enhanced team kickoff with specific instructions
            initial_team_prompt = f"""Team {team_name} Activation:

PROJECT CONTEXT: We are building a task management web application as specified in the technical requirements.

TEAM TASKS:
"""
            for task in all_tasks_for_team:
                initial_team_prompt += f"- {task['role']}: {task['task_id']} - {task['description']}\n"

            initial_team_prompt += f"""

EXECUTION INSTRUCTIONS:
1. {team_name}Manager: Start by analyzing all tasks and creating a detailed execution plan
2. Assign specific tasks to team members with clear deliverables
3. Team members: Use the create_directory and create_file tools to actually create all necessary files
4. Focus on creating production-ready, well-documented code
5. Include proper testing and documentation
6. Report completion status clearly

IMPORTANT: This is not a discussion - you must actually create the files and implement the functionality using the provided tools.

{team_name}Manager, please begin by analyzing the tasks and coordinating your team."""

            print(f"\nStarting {team_name} execution...")
            emit_status(f"Starting {team_name} execution with {len(team_agents)} agents")
            
            # Kick off the team execution
            result = group_run(group, task=initial_team_prompt)
            emit_status(f"Team {team_name} has completed its execution phase.")
            print(f"Team {team_name} completed")

        emit_status("\nAll teams have completed their tasks. Development phase complete.")
        
        # Show what was created
        print(f"\n📊 WORKSPACE SUMMARY:")
        print(list_files("."))
        emit_status("📊 Workspace summary generated")

    finally:
        # Return to original directory
        os.chdir(original_cwd)

# ----------------------------------------------------------------------------
# Main Execution Block
# ----------------------------------------------------------------------------

def run_autogen_system(tech_spec: str, repo_url: str = None):
    """Run the autonomous agent system with given spec content and optional repo url."""
    try:
        emit_status("System Initialized. Loading LLM configuration from file...")
        emit_status("LLM configuration loaded successfully.")
        emit_status("Loading technical specification...")
        emit_status("Technical specification loaded successfully.")

        approved_plan = dynamic_planning_and_validation(tech_spec)
        emit_status("Final Approved Plan received. Preparing for execution.")
        execute_development_plan(approved_plan)

        if repo_url:
            commit_to_github(repo_url, "autogen_workspace")

        emit_status("🎉 Autonomous development lifecycle complete! 🎉")
        print("\n🎉 Autonomous development lifecycle complete! 🎉")

        # Emit a final, definitive event to the frontend.
        if socketio:
            socketio.emit('lifecycle_complete', {'status': 'success'})

        return {"status": "success"}
    except Exception as e:
        error_message = f"\nAn unexpected error occurred: {e}"
        emit_status(error_message)
        print(error_message)
        return {"status": "error", "message": str(e)}
    finally:
        time.sleep(5)

# --- FastAPI app for frontend integration ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodegenRequest(BaseModel):
    repo_url: str|None = None
    spec_content: str | None = None
    spec_file_path: str | None = 'sample_tech_spec_v3.md'

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


# This is working version of the code

# @app.post("/api/update-spec-from-buffer")
# async def update_spec_from_buffer(request: Request):
#     try:
#         buffer = await request.body()
#         if not buffer:
#             raise HTTPException(status_code=400, detail="No buffer data received")
#         content = buffer.decode('utf-8')
        
#         spec_file_path = "sample_tech_spec_v3.md"
        
#         async with aiofiles.open(spec_file_path, "w", encoding="utf-8") as f:
#             await f.write(content)
        
#         # Start codegen in background thread
#         def start_codegen_bg():
#             global socketio
#             if socketio is None:
#                 socketio = start_dashboard_server_in_thread()
#                 import time
#                 max_retries = 10
#                 for i in range(max_retries):
#                  try:
#                      # Test if server is responsive
#                      time.sleep(1)
#                      break
#                  except Exception as e:
#                      if i == max_retries - 1:
#                          raise RuntimeError("Failed to start WebSocket server")
#                      continue
#             spec_content = read_spec_document(spec_file_path)
#             # repo_url = "https://github.com/goutamEximietas/codegen_repo.git"
#             repo_url=GITHUB_REPO_URL
#             run_autogen_system(spec_content, repo_url)
        
#         threading.Thread(target=start_codegen_bg, daemon=True).start()
        
#         return {
#             "status": "success",
#             "message": f"Successfully updated {spec_file_path} and started codegen in background",
#             "bytes_written": len(buffer)
#         }
        
#     except UnicodeDecodeError:
#         raise HTTPException(status_code=400, detail="Buffer contains invalid text data")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to write buffer to file: {str(e)}")











@app.post("/api/update-spec-from-buffer")
async def update_spec_from_buffer(request: Request):
    try:
        buffer = await request.body()
        if not buffer:
            raise HTTPException(status_code=400, detail="No buffer data received")
        content = buffer.decode('utf-8')
        
        spec_file_path = "sample_tech_spec_v3.md"
        
        async with aiofiles.open(spec_file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        google_doc_id = request.headers.get("project-id", "default_project")
        print(f"Google Project ID: {google_doc_id}")
        nodejs_api_url =NODEJS_BACKEND_BASE_URL  # Replace with your actual URL
        print(f"Node.js API URL: {nodejs_api_url}") 
        
        # Start codegen in background thread
        def start_codegen_bg():
            try:
                global socketio
                if socketio is None:
                    socketio = start_dashboard_server_in_thread()
                    time.sleep(5)
                
                spec_content = read_spec_document(spec_file_path)
                repo_url = GITHUB_REPO_URL
                
                marker_file = f"codegen_complete_{google_doc_id}.marker"
                if os.path.exists(marker_file):
                    os.remove(marker_file)
                
                monitor_thread = threading.Thread(
                    target=monitor_completion, 
                    args=(marker_file, nodejs_api_url, google_doc_id, repo_url),
                    daemon=True
                )
                monitor_thread.start()
                
                result = run_autogen_system(spec_content, repo_url)
                
                with open(marker_file, 'w') as f:
                    if result.get('status') == 'success':
                        f.write('SUCCESS')
                    else:
                        f.write('FAILED')
                
            except Exception as e:
                print(f"Error in codegen: {str(e)}")
                marker_file = f"codegen_complete_{google_doc_id}.marker"
                with open(marker_file, 'w') as f:
                    f.write('FAILED')
        
        threading.Thread(target=start_codegen_bg, daemon=True).start()
        
        return {
            "status": "success",
            "message": f"Successfully updated {spec_file_path} and started codegen in background",
            "bytes_written": len(buffer)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write buffer to file: {str(e)}")

def monitor_completion(marker_file, nodejs_api_url, google_doc_id, repo_url):
    """Monitor for completion marker file"""
    timeout = 1800  # 30 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if os.path.exists(marker_file):
            try:
                with open(marker_file, 'r') as f:
                    result = f.read().strip()
                
                if result == 'SUCCESS':
                    asyncio.run(update_nodejs_status(nodejs_api_url, google_doc_id, "COMPLETED", repo_url))
                    print(f"Code generation completed successfully for {google_doc_id}")
                else:
                    asyncio.run(update_nodejs_status(nodejs_api_url, google_doc_id, "PENDING", None))
                    print(f"Code generation failed for {google_doc_id}")
                
                os.remove(marker_file)
                return
                
            except Exception as e:
                print(f"Error reading marker file: {e}")
        
        time.sleep(5) 
    
    print(f"Timeout waiting for completion of {google_doc_id}")
    asyncio.run(update_nodejs_status(nodejs_api_url, google_doc_id, "PENDING", None))
    
    if os.path.exists(marker_file):
        os.remove(marker_file)

async def update_nodejs_status(nodejs_api_url: str, google_doc_id: str, status: str, github_repo_url: str = None):
    """Update Node.js with status"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "project_id": google_doc_id,
                "code_gen_status": status,
                "github_repo_url": github_repo_url
            }
            
            response = await client.post(
                f"{nodejs_api_url}/documents/update-codegen-status",
                json=payload,
                timeout=10.0
            )
            
            print(f"Updated Node.js status to {status}")
                
    except Exception as e:
        print(f"Error updating Node.js status: {str(e)}")















@app.post("/api/update-spec-json")
async def update_spec_json(request: Request):
    try:
        data = await request.json()
        content = data.get('content', '')
        
        if not content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        # Write asynchronously to the sample_tech_spec.md file
        spec_file_path = "sample_tech_spec.md"
        
        async with aiofiles.open(spec_file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        return {
            "status": "success",
            "message": f"Successfully updated {spec_file_path}",
            "characters_written": len(content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write content to file: {str(e)}")

@app.post("/api/start-codegen")
async def start_codegen(request: CodegenRequest):
    # spec_content = data.get("spec_content")
    # Doing this for testing purposes
    #TODO change this later by implemeting file reader function and providing json to the given api
    spec_content = read_spec_document(request.spec_file_path)
    repo_url = request.repo_url
    if not spec_content:
        return JSONResponse(status_code=400, content={"error": "spec_content is required"})
    # Start dashboard server if not already started
    global socketio
    if socketio is None:
        socketio = start_dashboard_server_in_thread()
        time.sleep(2)
    result = run_autogen_system(spec_content, repo_url)
    return JSONResponse(content=result)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # Run as API server
        socketio = start_dashboard_server_in_thread()
        time.sleep(2)
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        # CLI mode (legacy)
        socketio = start_dashboard_server_in_thread()
        time.sleep(2)
        parser = argparse.ArgumentParser(description="AutoGen Autonomous Agent System")
        parser.add_argument("--spec", type=str, required=True, help="Path to the technical specification document.")
        parser.add_argument("--repo-url", type=str, help="Optional: GitHub repository URL to commit the final code.")
        args = parser.parse_args()
        tech_spec = read_spec_document(args.spec)
        run_autogen_system(tech_spec, args.repo_url)
