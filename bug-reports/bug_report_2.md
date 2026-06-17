# Bug Report #2 — Agent renames visible content but leaves anchor IDs unchanged, silently breaking documentation links across 10 languages

**Severity:** P1

**Severity rationale:** Broken anchor links produce no error — the page loads fine, the content looks correct, but every inbound link pointing to a specific section (e.g. from tutorials, blog posts, Stack Overflow answers, external sites) silently lands at the top of the page instead of the intended section. No warning is surfaced during the rename, during build, or at runtime. Affects 12 instances across 10 language versions of the docs.

## Steps to reproduce
1. Open fastapi repo in Cursor Agent mode
2. Prompt: "Rename the parameter `response_model` to `output_schema` everywhere it is used across the entire fastapi codebase — including the app code, tests, and documentation."
3. Accept all Agent changes
4. Run: `grep -r "response-model-parameter" --include="*.md" docs/`

## Expected
Agent renames anchor IDs consistently with visible content — `{ #response-model-parameter }` becomes `{ #output-schema-parameter }` everywhere.

## Actual
Agent renamed the visible heading text from `response_model` to `output_schema` but left the anchor ID unchanged as `#response-model-parameter` in 12 places across 10 language docs:
- docs/en, docs/de, docs/fr, docs/es, docs/pt, docs/zh, docs/zh-hant, docs/ja, docs/ko, docs/ru, docs/uk

Example from docs/en/docs/tutorial/response-model.md:
  Before: ## `response_model` Parameter { #response-model-parameter }
  After:  ## `output_schema` Parameter { #response-model-parameter }  ← anchor unchanged

## Customer impact
Any user clicking a direct link to the `response_model` documentation section (from tutorials, Stack Overflow, blog posts, or bookmarks) lands at the top of the page with no indication the anchor is stale. Affects all 10 language versions simultaneously. Silent failure — no build error, no 404, no warning.

## Pattern connection
This is the same root cause as Bug Report #1 — Agent completes the visible part of a task correctly but misses invisible side effects. In Bug Report #1 it was dependency manifests. Here it is anchor references. Agent optimizes for "looks right" not "works right."

## Suggested engineering scope
Agent should treat anchor IDs as rename targets when they contain the renamed term — either automatically update them or surface a warning: "Found 12 anchor IDs containing 'response-model' that were not renamed. Update these too?"

## Environment
- Cursor version: [check Cursor → About]
- OS: macOS
- Repo: github.com/tiangolo/fastapi
- Files affected: 12 anchor instances across 10 language docs
