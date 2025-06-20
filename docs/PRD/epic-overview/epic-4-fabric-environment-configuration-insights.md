# Epic 4: Fabric Environment & Configuration Insights

- **Goal:** Provide MCP clients with the ability to list available Fabric models and strategies (strategy listing now moved to Epic 3), and to retrieve the current Fabric operational configuration securely.
- **Stories:**
- **Story 4.1: Implement `fabric_list_models` MCP Tool**
  - User Story: As an MCP Client Developer, I want to use the `fabric_list_models` tool to retrieve a list of all AI models configured and available in the connected Fabric instance (potentially categorized by vendor), so that I can inform users or make programmatic choices about model selection for pattern execution.
  - Acceptance Criteria:
    1. Tool implemented in `src/fabric_mcp/core.py`.
    2. Registered and advertised via `list_tools()` (no params, returns object) per `design.md`.
    3. Uses `FabricApiClient` for GET to Fabric API `/models/names`.
    4. Parses JSON response from Fabric API (expected: list of all models, map of models by vendor).
    5. MCP success response contains structured JSON (e.g., `{"models": [...], "vendors": {...}}`). Empty lists/objects if none.
    6. Returns structured MCP error for Fabric API errors or connection failures.
    7. Unit tests: mock `FabricApiClient` for success (models/vendors, empty), API errors.
    8. Integration tests: (vs. live local `fabric --serve`) verify response reflects local Fabric model config; test with no models if possible.
- **Story 4.2: Implement Secure `fabric_get_configuration` MCP Tool with Targeted Redaction**
  - User Story: As an MCP Client Developer, I want to use the `fabric_get_configuration` tool to retrieve the current operational configuration settings of the connected Fabric instance, **with assurances that sensitive values like API keys are redacted**, so that I can display relevant non-sensitive settings or understand the Fabric environment's setup securely.
  - Acceptance Criteria:
    1. Tool implemented in `src/fabric_mcp/core.py`. Registered and advertised via `list_tools()` (no params, returns map/object) per `design.md`.
    2. Uses `FabricApiClient` for GET to Fabric API `/config` endpoint.
    3. Parses JSON response (key-value map) from Fabric API. **Implements targeted redaction:** uses predefined list of sensitive key patterns (e.g., `*_API_KEY`, `*_TOKEN`). For matching keys with non-empty actual values, replaces value with `"[REDACTED_BY_MCP_SERVER]"`. Non-sensitive config values and empty string values are passed through.
    4. Returns MCP success response with processed (redacted where needed) JSON object.
    5. Returns structured MCP error for Fabric API errors or connection failures.
    6. Documentation notes redaction behavior and meaning of empty strings vs. redacted placeholders.
    7. Unit tests: mock `FabricApiClient`; test redaction logic (sensitive keys with values are redacted, sensitive keys with empty values passed as empty, non-sensitive keys passed through); test API errors.
    8. Integration tests: (vs. live local `fabric --serve` with dummy sensitive env vars set for Fabric) verify MCP response shows keys with `"[REDACTED_BY_MCP_SERVER]"` for sensitive values, and correct pass-through for non-sensitive/empty values.
