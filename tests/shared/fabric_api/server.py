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
from types import FrameType
from typing import Any, cast

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

# Mock strategies data that mimics real Fabric API responses
MOCK_STRATEGIES = [
    {
        "name": "default",
        "description": "Default strategy for pattern execution",
        "prompt": "Execute the pattern with default settings and balanced parameters",
    },
    {
        "name": "creative",
        "description": "Creative strategy with "
        "higher temperature for more varied output",
        "prompt": "Execute the pattern with enhanced creativity and diverse thinking",
    },
    {
        "name": "focused",
        "description": "Focused strategy with lower temperature for consistent output",
        "prompt": "Execute the pattern with precision and consistency in responses",
    },
    {
        "name": "analytical",
        "description": "Analytical strategy optimized for logical reasoning",
        "prompt": "Execute the pattern with emphasis on logical analysis and "
        "structured thinking",
    },
]

# Empty strategies for testing empty response case
EMPTY_STRATEGIES: list[dict[str, str]] = []

# Mock models data that mimics real Fabric API responses
MOCK_MODELS = {
    "models": [
        "gpt-4o",
        "gpt-3.5-turbo",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "llama2",
        "mixtral",
    ],
    "vendors": {
        "openai": ["gpt-4o", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "ollama": ["llama2", "mixtral"],
    },
}

# Empty models for testing empty response case
EMPTY_MODELS: dict[str, Any] = {
    "models": [],
    "vendors": {},
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
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


@app.get("/strategies")
async def list_strategies():
    """Return list of available Fabric strategies.

    This mimics the real Fabric API endpoint GET /strategies
    """
    logger.info("Serving strategies: %d strategies", len(MOCK_STRATEGIES))
    return MOCK_STRATEGIES


@app.get("/strategies/empty")
async def list_empty_strategies():
    """Return empty list of strategies for testing empty response case.

    This is a special test endpoint that returns an empty strategies list
    to verify the MCP tool handles the empty case correctly.
    """
    logger.info("Serving empty strategies list")
    return EMPTY_STRATEGIES


@app.get("/models/names")
async def list_models():
    """Return list of available Fabric models by vendor.

    This mimics the real Fabric API endpoint GET /models/names
    """
    logger.info("Serving models: %d total models", len(MOCK_MODELS["models"]))
    return MOCK_MODELS


@app.get("/models/names/empty")
async def list_empty_models():
    """Return empty list of models for testing empty response case.

    This is a special test endpoint that returns an empty models list
    to verify the MCP tool handles the empty case correctly.
    """
    logger.info("Serving empty models list")
    return EMPTY_MODELS


@app.post("/chat")
async def chat_endpoint(request_data: dict[str, Any]) -> StreamingResponse:
    """Execute a chat request with patterns (streaming).

    This mimics the real Fabric API endpoint POST /chat that handles
    Server-Sent Events (SSE) streaming responses. Enhanced to support
    execution control parameters for Story 3.3.
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

    prompt = cast(dict[str, Any], request_data["prompts"][0])
    if "patternName" not in prompt or not isinstance(prompt["patternName"], str):
        raise HTTPException(
            status_code=400,
            detail="Invalid request: 'patternName' must be present and a string",
        )
    # Extract pattern name with safe fallback and ensure it's a string
    pattern_name: str = prompt["patternName"]

    # Extract user input with safe fallback and ensure it's a string
    user_input: str = prompt["userInput"] if "userInput" in prompt else ""

    # Extract new execution control parameters
    model_name: str = prompt.get("model", "gpt-4o")
    vendor: str = prompt.get("vendor", "openai")
    strategy_name: str = prompt.get("strategyName", "")

    # Extract LLM parameters from root level
    temperature: float = request_data.get("temperature", 0.7)
    top_p: float = request_data.get("topP", 0.9)
    frequency_penalty: float = request_data.get("frequencyPenalty", 0.0)
    presence_penalty: float = request_data.get("presencePenalty", 0.0)

    if not pattern_name:
        raise HTTPException(
            status_code=400, detail="Invalid request: 'patternName' required"
        )

    # Validate model_name for testing parameter validation
    if model_name == "invalid_model":
        raise HTTPException(
            status_code=400, detail="Invalid model: model not supported"
        )

    # Validate strategy_name for testing parameter validation
    if strategy_name == "invalid_strategy":
        raise HTTPException(
            status_code=400, detail="Invalid strategy: strategy not found"
        )

    # Validate LLM parameters for testing parameter validation
    if not 0.0 <= temperature <= 2.0:
        raise HTTPException(
            status_code=400, detail="Invalid temperature: must be between 0.0 and 2.0"
        )
    if not 0.0 <= top_p <= 1.0:
        raise HTTPException(
            status_code=400, detail="Invalid top_p: must be between 0.0 and 1.0"
        )
    if not -2.0 <= frequency_penalty <= 2.0:
        raise HTTPException(
            status_code=400,
            detail="Invalid frequency_penalty: must be between -2.0 and 2.0",
        )
    if not -2.0 <= presence_penalty <= 2.0:
        raise HTTPException(
            status_code=400,
            detail="Invalid presence_penalty: must be between -2.0 and 2.0",
        )

    # Check if pattern exists (for testing specific patterns)
    if pattern_name not in MOCK_PATTERN_DETAILS and pattern_name != "test_pattern":
        raise HTTPException(
            status_code=404, detail=f"Pattern '{pattern_name}' not found"
        )

    logger.info(
        (
            "Chat endpoint: Running pattern '%s' with model '%s' (%s), "
            "strategy '%s', temp=%.1f"
        ),
        pattern_name,
        model_name,
        vendor,
        strategy_name or "",
        temperature,
    )

    def generate_sse_stream():
        """Generate Server-Sent Events stream with parameter-dependent responses."""
        # Create parameter-aware response content
        param_info: list[str] = []
        if strategy_name:
            param_info.append(f"strategy={strategy_name}")
        if model_name != "gpt-4o":
            param_info.append(f"model={model_name}")
        if temperature != 0.7:
            param_info.append(f"temp={temperature}")
        if top_p != 0.9:
            param_info.append(f"top_p={top_p}")
        if frequency_penalty != 0.0:
            param_info.append(f"freq_pen={frequency_penalty}")
        if presence_penalty != 0.0:
            param_info.append(f"pres_pen={presence_penalty}")

        param_str = f" [{', '.join(param_info)}]" if param_info else ""

        # Mock streaming response chunks that reflect execution parameters
        mock_content_chunks: list[str] = [
            f"Mock {pattern_name} output{param_str} for: ",
            user_input[:30] if user_input else "empty input",
            f"...\n\nExecuted with {vendor}/{model_name}",
        ]

        # Add strategy-specific content
        if strategy_name == "creative":
            mock_content_chunks.append(
                "\n\n*Creative strategy applied - more diverse output*"
            )
        elif strategy_name == "focused":
            mock_content_chunks.append(
                "\n\n*Focused strategy applied - precise output*"
            )
        elif strategy_name == "analytical":
            mock_content_chunks.append(
                "\n\n*Analytical strategy applied - logical reasoning*"
            )

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


@app.get("/config")
async def get_configuration() -> JSONResponse:
    """Get Fabric configuration with test data including sensitive values.

    This endpoint returns mock configuration data that includes various
    API keys and sensitive values to test the redaction functionality.
    """
    mock_config = {
        "openai_api_key": "sk-test123456789",
        "anthropic_api_key": "ant-test987654321",
        "google_api_key": "",  # Empty value to test pass-through
        "fabric_token": "fabric_secret_token_123",
        "database_secret": "db_secret_password",
        "user_password": "test_user_password",
        "empty_secret": "",  # Another empty value
        "api_timeout": 30,  # Non-sensitive numeric value
        "fabric_config_dir": "~/.config/fabric",  # Non-sensitive path
        "default_model": "gpt-4",  # Non-sensitive string
        "debug_mode": False,  # Non-sensitive boolean
        "allowed_patterns": ["summarize", "analyze"],  # Non-sensitive list
    }
    return JSONResponse(content=mock_config)


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
    def signal_handler(signum: int, _frame: FrameType | None) -> None:
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
