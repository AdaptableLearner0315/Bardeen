"""FastAPI backend for research assistant dashboard."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.agent.agent import create_agent
from src.evaluation.tracers.tool_tracer import ToolTracer
from src.evaluation.tracers.error_tracer import ErrorTracer
from src.evaluation.visualizer import ASCIIVisualizer
from src.evaluation.dataset import DatasetLoader
from src.shared.config import load_config


# Initialize FastAPI app
app = FastAPI(
    title="Research Assistant Dashboard",
    description="Web dashboard for LLM-powered research assistant with tool calling",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
config = None
agent = None
visualizer = ASCIIVisualizer(width=80)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    reset_conversation: bool = False
    mode: str = "normal"  # "normal" or "deep"

class ChatResponse(BaseModel):
    answer: str
    tool_calls: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    ascii_trace: str
    latency_ms: float
    mode: str = "normal"
    is_auto_detected: bool = False
    # New: Execution plan for explainability
    execution_plan: Optional[Dict[str, Any]] = None
    # New: Confidence indicator
    low_confidence: bool = False
    low_confidence_reason: Optional[str] = None

class EvaluationListResponse(BaseModel):
    evaluations: List[Dict[str, Any]]

class EvaluationDetailResponse(BaseModel):
    run_id: str
    timestamp: str
    dataset_size: int
    k_attempts: int
    temperature: float
    overall_pass_5: float
    overall_pass_10: float
    avg_consensus_strength: float
    avg_latency_ms: float
    error_recovery_rate: float
    category_metrics: Dict[str, Any]
    question_results: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup."""
    global config, agent

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. Agent will not function.")
        return

    config = load_config()
    agent = create_agent()
    print(f"✓ Agent initialized with tools: {', '.join(agent.get_available_tools())}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page."""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    index_path = frontend_dir / "index.html"

    if index_path.exists():
        with open(index_path, 'r') as f:
            return f.read()
    else:
        return {
            "message": "Research Assistant Dashboard API",
            "version": "1.0.0",
            "endpoints": {
                "chat": "/api/chat",
                "evaluations": "/api/evaluations",
                "health": "/api/health"
            }
        }


@app.get("/style.css")
async def serve_css():
    """Serve the CSS file."""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    css_path = frontend_dir / "style.css"

    if css_path.exists():
        with open(css_path, 'r') as f:
            return HTMLResponse(content=f.read(), media_type="text/css")
    else:
        raise HTTPException(status_code=404, detail="CSS file not found")


@app.get("/app.js")
async def serve_js():
    """Serve the JavaScript file."""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    js_path = frontend_dir / "app.js"

    if js_path.exists():
        with open(js_path, 'r') as f:
            return HTMLResponse(content=f.read(), media_type="application/javascript")
    else:
        raise HTTPException(status_code=404, detail="JavaScript file not found")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "available_tools": agent.get_available_tools() if agent else []
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for interacting with the research assistant.

    Returns answer with tool traces and ASCII visualization.
    Supports Normal mode (2-3 tools) and Deep mode (5-10 tools).
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API keys.")

    # Create tracers
    tracer = ToolTracer(attempt_number=1)
    error_tracer = ErrorTracer()

    # Determine max tool calls based on mode
    mode = request.mode.lower()
    if mode == "deep":
        max_tool_calls = 10  # Deep mode: 5-10 tools
        # Add system hint for deep research
        enhanced_message = f"""[DEEP RESEARCH MODE - Use 5-10 tools for comprehensive analysis]

{request.message}

Please provide a thorough, multi-faceted analysis using multiple tools:
- Use web search for current information
- Use Wikipedia for factual background
- Use calculator for any numerical analysis
- Use financial tools if relevant
- Cross-reference multiple sources for accuracy"""
    else:
        max_tool_calls = 3  # Normal mode: 2-3 tools
        enhanced_message = request.message

    # Get response from agent with planning
    start_time = datetime.now()
    answer, tool_traces, error_traces, execution_plan, mode_used, is_auto_detected = agent.ask_with_plan(
        question=enhanced_message,
        tracer=tracer,
        error_tracer=error_tracer,
        reset_conversation=request.reset_conversation,
        mode=None if mode == "auto" else mode  # None triggers auto-detection
    )
    end_time = datetime.now()
    latency_ms = (end_time - start_time).total_seconds() * 1000

    # Create ASCII trace
    from src.shared.models import AttemptResult
    attempt = AttemptResult(
        attempt_number=1,
        question_id="chat",
        final_answer=answer,
        tool_calls=tool_traces,
        errors=error_traces,
        total_latency_ms=latency_ms,
        is_correct=True,
        semantic_similarity=1.0,
        timestamp=datetime.now().isoformat()
    )
    ascii_trace = visualizer.visualize_attempt(attempt)

    # Convert traces to dict for JSON serialization
    tool_calls_dict = [
        {
            "tool_name": t.tool_name,
            "params": t.params,
            "result": str(t.result)[:200] if t.result else None,
            "status": t.status.value,
            "latency_ms": t.latency_ms,
            "llm_reasoning": t.llm_reasoning
        }
        for t in tool_traces
    ]

    errors_dict = [
        {
            "tool_name": e.tool_name,
            "error_message": e.error_message,
            "recovery_action": e.recovery_action,
            "recovery_success": e.recovery_success
        }
        for e in error_traces
    ]

    # Check for low confidence marker
    low_confidence = False
    low_confidence_reason = None
    clean_answer = answer

    if answer.startswith("[LOW_CONFIDENCE:"):
        low_confidence = True
        # Extract reason and clean answer
        if "TOOL_LIMIT_REACHED]" in answer:
            low_confidence_reason = "Tool limit reached. Increase tool limit for more comprehensive results."
            clean_answer = answer.split("]\n", 1)[1] if "]\n" in answer else answer

    return ChatResponse(
        answer=clean_answer,
        tool_calls=tool_calls_dict,
        errors=errors_dict,
        ascii_trace=ascii_trace,
        latency_ms=latency_ms,
        mode=mode_used,
        is_auto_detected=is_auto_detected,
        execution_plan=execution_plan.to_dict() if execution_plan else None,
        low_confidence=low_confidence,
        low_confidence_reason=low_confidence_reason
    )


@app.get("/api/evaluations", response_model=EvaluationListResponse)
async def list_evaluations():
    """List all evaluation runs."""
    results_dir = Path("data/results")

    if not results_dir.exists():
        return EvaluationListResponse(evaluations=[])

    evaluations = []
    for result_file in sorted(results_dir.glob("eval_*.json"), reverse=True):
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                evaluations.append({
                    "run_id": data["run_id"],
                    "timestamp": data["timestamp"],
                    "dataset_size": data["dataset_size"],
                    "overall_pass_5": data["overall_pass_5"],
                    "overall_pass_10": data["overall_pass_10"],
                    "avg_consensus_strength": data["avg_consensus_strength"]
                })
        except Exception as e:
            print(f"Error reading {result_file}: {e}")
            continue

    return EvaluationListResponse(evaluations=evaluations)


@app.get("/api/evaluations/{run_id}", response_model=EvaluationDetailResponse)
async def get_evaluation(run_id: str):
    """Get detailed results for a specific evaluation run."""
    result_file = Path(f"data/results/{run_id}.json")

    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")

    try:
        with open(result_file, 'r') as f:
            data = json.load(f)

        return EvaluationDetailResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading evaluation: {e}")


@app.get("/api/dataset")
async def get_dataset():
    """Get the evaluation dataset."""
    dataset_path = Path("data/dataset.json")

    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        loader = DatasetLoader(dataset_path)
        questions = loader.load()
        stats = loader.get_statistics()

        return {
            "metadata": loader.metadata,
            "statistics": stats,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "category": q.category,
                    "difficulty": q.difficulty,
                    "expected_tools": q.expected_behavior.get("tools", [])
                }
                for q in questions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {e}")


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    if not agent:
        await websocket.send_json({
            "type": "error",
            "message": "Agent not initialized. Check API keys."
        })
        await websocket.close()
        return

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            reset_conversation = data.get("reset_conversation", False)

            # Send acknowledgment
            await websocket.send_json({
                "type": "status",
                "message": "Processing your question..."
            })

            # Create tracers
            tracer = ToolTracer(attempt_number=1)
            error_tracer = ErrorTracer()

            # Get response
            start_time = datetime.now()
            answer, tool_traces, error_traces = agent.ask(
                question=message,
                tracer=tracer,
                error_tracer=error_tracer,
                reset_conversation=reset_conversation
            )
            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            # Send response
            await websocket.send_json({
                "type": "response",
                "answer": answer,
                "tool_calls": [
                    {
                        "tool_name": t.tool_name,
                        "params": t.params,
                        "status": t.status.value,
                        "latency_ms": t.latency_ms
                    }
                    for t in tool_traces
                ],
                "latency_ms": latency_ms
            })

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=your_key_here")
        exit(1)

    print("Starting Research Assistant Dashboard...")
    print("Access the dashboard at: http://localhost:8000")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)
