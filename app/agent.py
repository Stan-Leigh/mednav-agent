import re
from typing import Any
import os
import sys
from google.adk.workflow import Workflow, node, FunctionNode, START
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.adk.apps import App, ResumabilityConfig
from google.adk.models import Gemini
from google.genai import types
import uuid
from google.adk.models import LlmResponse

from app.config import config

# Initialize Gemini Model using config
gemini_model = Gemini(
    model=config.model,
    retry_options=types.HttpRetryOptions(
        attempts=6,
        initial_delay=2.0,
        max_delay=60.0,
        exp_base=2.0,
    ),
)

# Initialize MCP Toolset for local stdio server
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp_server_path = os.path.join(current_dir, "mcp_server.py")

mednav_mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_path],
        )
    )
)

# 1. Specialized LlmAgents with wired McpToolset
med_jargon_agent = LlmAgent(
    name="MedJargonAgent",
    model=gemini_model,
    instruction="""You are a medical jargon translation specialist. Your job is to translate complex medical terminology (e.g., 'erythema', 'myocardial infarction') into simple, everyday language that a layperson can easily understand. Be empathetic, clear, and concise. Use your explain_medical_term tool to find definitions for medical terms. Avoid using other complex terms in your explanation. If you don't know a term, explain what you do know or suggest consulting a physician. Always be warm and patient. Every response MUST include a standard medical disclaimer: 'Disclaimer: This information is for educational purposes only and does not constitute medical advice.'""",
    tools=[mednav_mcp_toolset]
)

clinical_trial_agent = LlmAgent(
    name="ClinicalTrialAgent",
    model=gemini_model,
    instruction="""You are a clinical trials specialist. Your job is to help patients understand clinical trials, including eligibility criteria, trial phases, and outcomes. Use your search_clinical_trials tool to search for trials and get_trial_details tool to fetch details. Translate any complex trial details into patient-friendly language.""",
    tools=[mednav_mcp_toolset]
)

# 2. Orchestrator Agent
mednav_orchestrator = LlmAgent(
    name="mednav_orchestrator",
    model=gemini_model,
    instruction="""You are the MedNav Orchestrator. Your role is to help patients understand medical queries.
    You have two sub-agents at your disposal:
    1. MedJargonAgent: Use this agent to translate complex medical terms and explanations into plain English.
    2. ClinicalTrialAgent: Use this agent to analyze and explain clinical trials, search for trials, or retrieve details about trials.

    Always route user requests to the appropriate agent. If a query requires both terminology translation and clinical trial information, coordinate with both.
    When you receive the results, compile them into a coherent, simple, and reassuring response for the patient.
    Every response MUST include a standard medical disclaimer: 'Disclaimer: This information is for educational purposes only and does not constitute medical advice. Please consult a healthcare professional for medical concerns.'
    """,
    tools=[AgentTool(med_jargon_agent), AgentTool(clinical_trial_agent)]
)

# 3. Security Checkpoint Function Node
def security_checkpoint(ctx: Context, node_input: types.Content) -> Event:
    import json
    query = ""
    if hasattr(node_input, "parts") and node_input.parts:
        query = "".join(part.text for part in node_input.parts if part.text)
    elif isinstance(node_input, str):
        query = node_input
    
    # PII scrubbing
    cleaned_query = query
    if config.pii_redaction_enabled:
        # Email
        cleaned_query = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', cleaned_query)
        # Phone
        cleaned_query = re.sub(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b', '[REDACTED_PHONE]', cleaned_query)
        # SSN / Medical ID
        cleaned_query = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_ID]', cleaned_query)
        cleaned_query = re.sub(r'\bMRN\d{6,8}\b', '[REDACTED_MRN]', cleaned_query)

    # Prompt injection check
    injection_detected = False
    if config.injection_detection_enabled:
        injection_keywords = ["ignore previous instructions", "bypass security", "system prompt", "developer mode"]
        for keyword in injection_keywords:
            if keyword in cleaned_query.lower():
                injection_detected = True
                break

    if injection_detected:
        audit_log = {
            "severity": "CRITICAL",
            "event": "PROMPT_INJECTION",
            "message": "Prompt injection attempt detected.",
            "query": query
        }
        print(json.dumps(audit_log))
        return Event(
            output="Security Violation: The request contains potential prompt injection and cannot be processed.",
            route="security_failed"
        )
    
    # Domain-specific medical advice check
    medical_safety_violation = False
    medical_safety_keywords = ["diagnose me", "what disease do i have", "prescribe", "give me a prescription", "what medicine should i take for"]
    for keyword in medical_safety_keywords:
        if keyword in cleaned_query.lower():
            medical_safety_violation = True
            break
            
    if medical_safety_violation:
        audit_log = {
            "severity": "WARNING",
            "event": "MEDICAL_SAFETY_VIOLATION",
            "message": "User requested diagnosis or prescription.",
            "query": cleaned_query
        }
        print(json.dumps(audit_log))
        return Event(
            output="Medical Safety Boundary: MedNav Agent cannot diagnose conditions or prescribe medications. Please consult a healthcare professional. For explaining terminology or clinical trials, please rephrase your question.",
            route="security_failed"
        )

    if cleaned_query != query:
        audit_log = {
            "severity": "WARNING",
            "event": "PII_REDACTED",
            "message": "PII scrubbed from user input.",
            "cleaned_query": cleaned_query
        }
        print(json.dumps(audit_log))
    else:
        audit_log = {
            "severity": "INFO",
            "event": "SECURITY_PASSED",
            "message": "Security check passed successfully."
        }
        print(json.dumps(audit_log))
        
    return Event(output=cleaned_query, route="security_passed", state={"cleaned_query": cleaned_query})

# 4. Human Review Function Node (Human-in-the-Loop)
@node(rerun_on_resume=True)
async def human_review(ctx: Context, node_input: Any) -> Event:
    print(f"[DEBUG] human_review called. node_input: {node_input} (type: {type(node_input)}), resume_inputs: {ctx.resume_inputs}, state: {ctx.state}")
    orchestrator_text = ""
    if hasattr(node_input, "parts") and node_input.parts:
        orchestrator_text = "".join(part.text for part in node_input.parts if part.text)
    elif isinstance(node_input, str):
        orchestrator_text = node_input
    
    # Store orchestrator output in state so we don't lose it on resume
    if "orchestrator_text" not in ctx.state:
        ctx.state["orchestrator_text"] = orchestrator_text
    else:
        orchestrator_text = ctx.state["orchestrator_text"]

    if not ctx.resume_inputs or "approve_guide" not in ctx.resume_inputs:
        # Request human review
        yield RequestInput(
            interrupt_id="approve_guide",
            message=f"--- REVIEW REQ ---\nGenerated medical explanation:\n\n{orchestrator_text}\n\nDo you approve presenting this guide to the patient? (yes/no)"
        )
        return
    
    res = ctx.resume_inputs.get("approve_guide", "")
    if isinstance(res, dict):
        approval = res.get("approve_guide", "")
    else:
        approval = str(res)
    approval = approval.strip().lower()
    
    print(f"[AUDIT LOG] [INFO] Human review decision received: {approval}")
    if approval == "yes":
        yield Event(output=orchestrator_text)
    else:
        yield Event(output="Revision Requested: The generated guide was not approved by the reviewer. Please try rephrasing your query or providing more context.")

# 5. Final Response Node
def final_response(node_input: str):
    # Render in ADK web UI
    yield Event(content=types.Content(role='model', parts=[types.Part.from_text(text=node_input)]))
    yield Event(output=node_input)

# 6. Workflow Definition
edges = [
    ('START', security_checkpoint),
    (security_checkpoint, {"security_passed": mednav_orchestrator, "security_failed": final_response}),
    (mednav_orchestrator, human_review),
    (human_review, final_response),
]

root_agent = Workflow(
    name="mednav_workflow",
    edges=edges,
)

# 7. App instance with Resumability Config for HITL
app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True)
)
