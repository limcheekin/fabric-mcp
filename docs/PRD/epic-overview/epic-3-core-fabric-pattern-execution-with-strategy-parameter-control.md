# Epic 3: Core Fabric Pattern Execution with Strategy & Parameter Control

- **Goal:** Allow MCP clients to execute specified Fabric patterns, apply operational strategies, control execution with various parameters (model, temperature, variables, attachments), and receive output, including support for streaming.
- **Stories:**
  - **Story 3.1: Implement Basic `fabric_run_pattern` Tool (Non-Streaming)**
    - User Story: As an MCP Client Developer, I want to use the `fabric_run_pattern` tool to execute a named Fabric pattern with optional `input_text`, and receive its complete output in a non-streaming manner, so that I can integrate Fabric's fundamental pattern execution capability.
    - Acceptance Criteria:
            1. Tool implemented in `src/fabric_mcp/core.py` for basic, non-streaming execution.
            2. Advertised via `list_tools()` with at least `pattern_name: string (req)`, `input_text: string (opt)`, `stream: boolean (opt, default:false)`.
            3. Invokes Fabric API POST (e.g., `/chat`) via `FabricApiClient` with `pattern_name`, `input_text`; request is non-streaming.
            4. Waits for complete Fabric API response, parses LLM output.
            5. Returns MCP success with complete LLM output.
            6. Returns MCP client-side error if `pattern_name` missing.
            7. Returns structured MCP error for Fabric API errors or connection errors.
            8. Unit tests: mock `FabricApiClient` for correct request (name, input, non-streaming), successful response parsing, API errors, missing MCP params.
            9. Integration tests: (vs. live local `fabric --serve`) execute simple pattern with name/input, verify complete non-streaming output; test non-existent pattern for MCP error.
  - **Story 3.2: Implement `fabric_list_strategies` MCP Tool**
    - User Story: As an MCP Client Developer, I want to use the `fabric_list_strategies` tool to retrieve a list of all available operational strategies from the connected Fabric instance, so that end-users can be aware of or select different strategies if patterns support them.
    - Acceptance Criteria:
            1. Tool implemented in `src/fabric_mcp/core.py`.
            2. Registered and advertised via `list_tools()` (no params, returns list of objects) per `design.md`.
            3. Uses `FabricApiClient` for GET to Fabric API `/strategies` endpoint.
            4. Parses JSON response (array of strategy objects with `name`, `description`, `prompt`).
            5. MCP success response contains JSON array of strategy objects (name, description, prompt). Empty list if none.
            6. Returns structured MCP error for Fabric API errors or connection failures.
            7. Unit tests: mock `FabricApiClient` for success (list of strategies, empty list), API errors.
            8. Integration tests: (vs. live local `fabric --serve` with strategies configured) verify correct list of strategies; test with no strategies for empty list.
  - **Story 3.3: Enhance `fabric_run_pattern` with Execution Control Parameters (Model, LLM Params, Strategy)**
    - User Story: As an MCP Client Developer, I want to enhance the `fabric_run_pattern` tool to allow specifying optional `model_name`, LLM tuning parameters (`temperature`, `top_p`, `presence_penalty`, `frequency_penalty`), and an optional `strategy_name` (selected from those available via `fabric_list_strategies`) so that I can have finer control over the pattern execution by the Fabric instance.
    - Acceptance Criteria:
            1. `fabric_run_pattern` definition via `list_tools()` updated for optional `model_name` (str), `temperature` (float), `top_p` (float), `presence_penalty` (float), `frequency_penalty` (float), `strategy_name` (str).
            2. Tool parses these optional params; if provided, includes them in Fabric API request (e.g., `PromptRequest.Model`, `ChatOptions`, `PromptRequest.StrategyName`). Omits if not provided.
            3. Integration tests: verify `model_name` override, `strategy_name` application (e.g., "cot") affects output, LLM tuning params affect output.
            4. Returns structured MCP error if Fabric API rejects these parameters.
            5. Unit tests: mock `FabricApiClient` for request construction with these params (individual, mixed, omitted), API errors for invalid params.
            6. Integration tests: (vs. live local `fabric --serve`) test `model_name` override, `strategy_name` application, (if feasible) LLM tuning param effect; test invalid model/strategy names for MCP error.
  - **Story 3.4: Implement Streaming Output for `fabric_run_pattern` Tool**
    - User Story: As an MCP Client Developer, I want the `fabric_run_pattern` tool to support a `stream` parameter, which, when true, provides the Fabric pattern's output as a real-time stream, so that I can build more responsive and interactive client experiences.
    - Acceptance Criteria:
            1. Tool processes optional `stream: boolean` MCP parameter. `stream=true` initiates streaming; `stream=false`/omitted uses non-streaming.
            2. When `stream=true`, `FabricApiClient` requests streaming response from Fabric API. **Client MUST use HTTP streaming mechanism to consume and parse streaming response chunks from Fabric API.**
            3. Data chunks from Fabric API streaming response relayed to MCP client via `FastMCP` streaming over active transport (stdio, Streamable HTTP).
            4. Real-time data transfer with minimal latency.
            5. Handles errors during Fabric API streaming response (e.g., invalid chunk, Fabric error mid-stream) by terminating MCP stream and sending MCP error.
            6. Unit tests: mock `FabricApiClient` for `stream=true` configuring streaming consumption, receiving/processing streaming chunks, stream termination (success/error).
            7. Integration tests: (vs. live local `fabric --serve`) execute streaming pattern with `stream=true`, verify multiple chunks and correct assembled output; confirm `stream=false` still works.
  - **Story 3.5: Add Support for `variables` and `attachments` to `fabric_run_pattern` Tool**
    - User Story: As an MCP Client Developer, I want to be able to pass `variables` (as a map of key-value strings) and `attachments` (as a list of file paths/URLs) to the `fabric_run_pattern` tool, so that I can execute more complex and context-rich Fabric patterns.
    - Acceptance Criteria:
            1. `fabric_run_pattern` definition via `list_tools()` updated for optional `variables` (map[string]string) and `attachments` (list[string]).
            2. If `variables` provided, parsed and included in Fabric API request payload. Omitted if not provided.
            3. If `attachments` provided, parsed and list of strings included in Fabric API request. Omitted if not provided. (Server only passes strings, Fabric resolves paths/URLs).
            4. Integration tests (mock Fabric API): verify `FabricApiClient` sends `variables` and `attachments` in requests. (Live Fabric API test if pattern exists to demonstrate use).
            5. Returns structured MCP error if Fabric API errors on `variables`/`attachments` processing.
            6. Unit tests: mock `FabricApiClient` for request construction with `variables` (empty, populated), `attachments` (empty, populated), both; simulate Fabric API errors.
            7. Integration tests: (vs. live local `fabric --serve`, ideally with test pattern) execute with `variables`/`attachments` and confirm (if possible) Fabric received/used them.
