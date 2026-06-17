# Bug Report #3 — Tab completion uses stale index and suggests wrong parameter in decorator context

**Severity:** P1

**Severity rationale:** Two compounding failures in a single Tab completion event. First, Tab suggests a parameter name from a stale index — ignoring a rename that was applied across 252 files moments earlier. Second, it suggests the semantically wrong parameter for the context. A developer accepting this suggestion ships incorrect API behavior with no warning — `response_class` changes the global response type, `response_model` (or `output_schema`) defines the return schema. Silent functional difference.

## Steps to reproduce
1. Open fastapi repo in Cursor after running Agent rename of `response_model` → `output_schema` across entire codebase
2. Create a new file: `fastapi/health_extended.py`
3. Type manually (do not paste):
```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health/detailed", response_
```
4. Stop after `response_` and wait for Tab suggestion

## Expected
- Parameter name: `output_schema` (the renamed parameter now used across the codebase)
- Or at minimum: `response_model` with correct semantic context
- Suggested value: a Pydantic model from the existing codebase

## Actual
Tab suggested: `response_class=JSONResponse`
- Wrong parameter name — `response_class` is for changing response format globally, not defining a return schema
- Stale parameter name — suggested `response_model` (old name) not `output_schema` (renamed 10 minutes earlier across 252 files)
- Wrong value — `JSONResponse` is not a schema model, it's a response class

## Screenshot
[Screenshot attached — shows `response_class=JSONResponse` suggestion in decorator]

## Customer impact
Developer accepts Tab suggestion and ships `response_class=JSONResponse` instead of `response_model=SomeSchema`. The route works but skips FastAPI's automatic response validation, serialization, and OpenAPI schema generation — a silent functional regression with no error surfaced at development or runtime.

## Pattern connection
Connects to Bug Reports #1 and #2 — Agent and Tab completion both optimize for surface-level correctness. Tab completion reads from a stale index rather than the live codebase state, meaning any Agent-driven rename is invisible to Tab completion until the index refreshes. The two features are not in sync.

## Suggested engineering scope
1. Tab completion index should refresh after Agent applies bulk changes — or at minimum flag that the index may be stale
2. Tab completion should use semantic context (inside a @router.get() decorator) to filter parameter suggestions to those valid for that specific function signature
3. `response_class` and `response_model` should not be interchangeable suggestions — they have fundamentally different behaviors

## Environment
- Cursor version: [check Cursor → About]
- OS: macOS
- Python: 3.14.3
- Repo: github.com/tiangolo/fastapi
- Screenshot: yes
