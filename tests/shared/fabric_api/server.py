"""Mock Fabric API Server for Integration Testing.

This module provides a minimal FastAPI-based server that mimics the Fabric REST API
for integration testing purposes. It serves the same endpoints that the real Fabric
API would serve, but with predictable mock data.
"""

import argparse
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from fabric_mcp import __version__ as fabric_mcp_version

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data that mimics real Fabric API responses
MOCK_PATTERNS = [
    "analyze_claims",
    "create_story",
    "summarize",
    "extract_insights",
    "check_grammar",
    "create_outline",
]

MOCK_PATTERN_DETAILS = {
    "analyze_claims": {
        "Name": "analyze_claims",
        "Description": "Analyze and fact-check claims in text",
        "Pattern": (
            "# IDENTITY and PURPOSE\n\nYou are an expert fact checker and "
            "truth evaluator. Your role is to analyze claims and statements to "
            "determine their accuracy, reliability, and truthfulness.\n\n"
            "Take a step back and think step-by-step about how to achieve the "
            "best possible results by following the steps below.\n\n## STEPS\n\n"
            "- Carefully read through the entire input to understand the claims "
            "being made\n- Identify specific factual claims that can be verified\n"
            "- Research each claim using reliable sources\n"
            "- Evaluate the credibility of sources and evidence\n"
            "- Determine the accuracy of each claim\n"
            "- Note any biases or logical fallacies present\n\n"
            "## OUTPUT INSTRUCTIONS\n\n- Only output Markdown\n"
            "- Provide a clear assessment for each major claim\n"
            "- Include confidence levels (High/Medium/Low) for your assessments\n"
            "- Cite sources when possible\n"
            "- Be objective and avoid personal opinions\n\n## INPUT\n\nINPUT:"
        ),
    },
    "create_story": {
        "Name": "create_story",
        "Description": "Create engaging stories from prompts",
        "Pattern": (
            "# IDENTITY and PURPOSE\n\nYou are an expert storyteller with "
            "the ability to create compelling, engaging narratives from any "
            "prompt or concept.\n\nTake a step back and think step-by-step "
            "about how to achieve the best possible results by following the "
            "steps below.\n\n## STEPS\n\n- Understand the core concept or "
            "prompt provided\n- Develop interesting characters with clear "
            "motivations\n- Create a compelling plot structure with conflict "
            "and resolution\n- Build an engaging setting that supports the "
            "story\n- Write with vivid descriptions and dialogue\n"
            "- Ensure the story has a satisfying conclusion\n\n"
            "## OUTPUT INSTRUCTIONS\n\n- Only output Markdown\n"
            "- Create a complete story with beginning, middle, and end\n"
            "- Use engaging dialogue and descriptive language\n"
            "- Keep the story appropriate for the intended audience\n"
            "- Aim for 500-1500 words unless otherwise specified\n\n"
            "## INPUT\n\nINPUT:"
        ),
    },
    "summarize": {
        "Name": "summarize",
        "Description": "Create concise summaries of text content",
        "Pattern": (
            "# IDENTITY and PURPOSE\n\nYou are an expert content summarizer. "
            "Your role is to analyze text and create concise, informative "
            "summaries that capture the essential information.\n\n"
            "Take a step back and think step-by-step about how to achieve the "
            "best possible results by following the steps below.\n\n"
            "## STEPS\n\n- Read through the entire text to understand the main "
            "topics\n- Identify the most important points and key messages\n"
            "- Note any supporting details that are crucial for understanding\n"
            "- Organize the information logically\n"
            "- Create a coherent summary that flows well\n"
            "- Ensure all critical information is preserved\n\n"
            "## OUTPUT INSTRUCTIONS\n\n- Only output Markdown\n"
            "- Create a summary that is 20-30% of the original length\n"
            "- Use clear, concise language\n"
            "- Maintain the original tone and intent\n"
            "- Include bullet points for key takeaways if appropriate\n\n"
            "## INPUT\n\nINPUT:"
        ),
    },
    "extract_insights": {
        "Name": "extract_insights",
        "Description": "Extract key insights and patterns from data or text",
        "Pattern": (
            "# IDENTITY and PURPOSE\n\nYou are an expert analyst "
            "specializing in extracting meaningful insights and patterns from "
            "data, text, or other information sources.\n\n## STEPS\n\n"
            "- Analyze the input for patterns, trends, and anomalies\n"
            "- Identify key insights and their implications\n"
            "- Look for correlations and relationships\n"
            "- Extract actionable recommendations\n\n"
            "## OUTPUT INSTRUCTIONS\n\n- Only output Markdown\n"
            "- Present insights in order of importance\n"
            "- Support findings with evidence from the input\n"
            "- Include actionable recommendations where appropriate\n\n"
            "## INPUT\n\nINPUT:"
        ),
    },
    "check_grammar": {
        "Name": "check_grammar",
        "Description": "Check and correct grammar, spelling, and style",
        "Pattern": (
            "# IDENTITY and PURPOSE\n\nYou are an expert proofreader and "
            "editor with excellent command of grammar, spelling, punctuation, "
            "and style.\n\n## STEPS\n\n- Review text for grammatical errors\n"
            "- Check spelling and punctuation\n"
            "- Evaluate sentence structure and clarity\n"
            "- Suggest improvements for style and readability\n\n"
            "## OUTPUT INSTRUCTIONS\n\n- Only output Markdown\n"
            "- Provide corrected text\n- Explain major changes made\n"
            "- Maintain the author's voice and intent\n\n## INPUT\n\nINPUT:"
        ),
    },
    "create_outline": {
        "Name": "create_outline",
        "Description": "Create structured outlines for documents or presentations",
        "Pattern": (
            "# IDENTITY and PURPOSE\n\nYou are an expert at creating clear, "
            "logical outlines for documents, presentations, and other "
            "structured content.\n\n## STEPS\n\n"
            "- Understand the main topic and objectives\n"
            "- Identify key themes and subtopics\n"
            "- Organize information hierarchically\n"
            "- Ensure logical flow and progression\n\n"
            "## OUTPUT INSTRUCTIONS\n\n- Only output Markdown\n"
            "- Use proper heading hierarchy (##, ###, etc.)\n"
            "- Include brief descriptions for each section\n"
            "- Ensure comprehensive coverage of the topic\n\n"
            "## INPUT\n\nINPUT:"
        ),
    },
}


@asynccontextmanager
async def lifespan(_app: FastAPI):  # type: ignore[misc]
    """Application lifespan manager."""
    logger.info("Mock Fabric API server starting up...")
    yield
    logger.info("Mock Fabric API server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Mock Fabric API",
    description="Mock Fabric REST API server for integration testing",
    version=fabric_mcp_version,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"message": "Mock Fabric API Server", "status": "running"}


@app.get("/patterns/names")
async def list_pattern_names():
    """Return list of available pattern names.

    This mimics the real Fabric API endpoint GET /patterns/names
    """
    logger.info("Serving pattern names: %s", MOCK_PATTERNS)
    return MOCK_PATTERNS


@app.get("/patterns/{pattern_name}")
async def get_pattern_details(pattern_name: str):
    """Get details for a specific pattern.

    This mimics the real Fabric API endpoint GET /patterns/{name}
    """
    if pattern_name not in MOCK_PATTERN_DETAILS:
        raise HTTPException(
            status_code=404, detail=f"Pattern '{pattern_name}' not found"
        )

    logger.info("Serving pattern details for: %s", pattern_name)
    return MOCK_PATTERN_DETAILS[pattern_name]


@app.post("/patterns/{pattern_name}/run")
async def run_pattern(pattern_name: str, request_data: dict[str, Any]):
    """Execute a pattern with input text.

    This mimics the real Fabric API endpoint POST /patterns/{name}/run
    """
    if pattern_name not in MOCK_PATTERN_DETAILS:
        raise HTTPException(
            status_code=404, detail=f"Pattern '{pattern_name}' not found"
        )

    input_text = request_data.get("input", "")
    logger.info(
        "Running pattern '%s' with input length: %d", pattern_name, len(input_text)
    )

    # Generate mock response based on pattern
    mock_response = {
        "output_format": "text",
        "output_text": f"Mock {pattern_name} output for input: {input_text[:50]}...",
        "model_used": "gpt-4o",
        "tokens_used": len(input_text) + 100,
        "execution_time_ms": 1250,
    }

    return mock_response


@app.post("/chat")
async def chat_endpoint(request_data: dict[str, Any]):
    """Execute a chat request with patterns (streaming).

    This mimics the real Fabric API endpoint POST /chat that handles
    Server-Sent Events (SSE) streaming responses.
    """

    # Validate request structure
    if "prompts" not in request_data or not isinstance(request_data["prompts"], list):
        raise HTTPException(
            status_code=400, detail="Invalid request: 'prompts' array required"
        )

    if not request_data["prompts"]:
        raise HTTPException(
            status_code=400, detail="Invalid request: at least one prompt required"
        )

    prompt: dict[str, Any] = request_data["prompts"][0]  # type: ignore[assignment]

    # Extract pattern name with safe fallback and ensure it's a string
    pattern_name: str = ""
    if "patternName" in prompt and prompt["patternName"]:
        pattern_name = str(prompt["patternName"])  # type: ignore[arg-type]

    # Extract user input with safe fallback and ensure it's a string
    user_input: str = ""
    if "userInput" in prompt and prompt["userInput"]:
        user_input = str(prompt["userInput"])  # type: ignore[arg-type]

    if not pattern_name:
        raise HTTPException(
            status_code=400, detail="Invalid request: 'patternName' required"
        )

    # Check if pattern exists (for testing specific patterns)
    if pattern_name not in MOCK_PATTERN_DETAILS and pattern_name != "test_pattern":
        raise HTTPException(
            status_code=404, detail=f"Pattern '{pattern_name}' not found"
        )

    logger.info(
        "Chat endpoint: Running pattern '%s' with input length: %d",
        pattern_name,
        len(user_input),
    )

    def generate_sse_stream():
        """Generate Server-Sent Events stream."""
        # Mock streaming response chunks
        mock_content_chunks: list[str] = [
            f"Mock {pattern_name} output for: ",
            user_input[:30] if user_input else "empty input",
            "...\n\nThis is a test response from the mock Fabric API server.",
        ]

        # Send content chunks
        for chunk in mock_content_chunks:
            sse_data: dict[str, str] = {
                "type": "content",
                "content": chunk,
                "format": "text",
            }
            yield f"data: {json.dumps(sse_data)}\n\n"

        # Send completion signal
        completion_data: dict[str, str] = {"type": "complete"}
        yield f"data: {json.dumps(completion_data)}\n\n"

    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Any, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    if isinstance(exc, HTTPException):
        # If it's an HTTPException, we can return it directly
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def run_server(host: str = "127.0.0.1", port: int = 8080):
    """Run the mock Fabric API server."""
    logger.info("Starting Mock Fabric API server on %s:%s", host, port)

    # Handle shutdown signals gracefully
    def signal_handler(signum: int, _frame: Any) -> None:  # type: ignore[misc]
        logger.info("Received signal %s, shutting down...", signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure uvicorn
    config = uvicorn.Config(
        app=app, host=host, port=port, log_level="info", access_log=True, loop="asyncio"
    )

    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Fabric API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")

    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
