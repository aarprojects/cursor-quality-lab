# Day 1 Observations — Cursor Bug Hunting

## Repo: tiangolo/fastapi
## Date: June 16, 2025

---

## Observation 1
**Time:** Today
**Repo:** fastapi
**Feature used:** Agent mode
**Prompt given:** "Add a /health endpoint. Update the app, docs, and tests."
**What happened:** Agent added `timeout` config to pytest.ini without installing pytest-timeout — caused INTERNALERROR killing entire test collection
**What I expected:** Working config or no config change
**Severity:** P1
**Became:** bug_report_1.md

## Observation 2
**Time:** Today
**Repo:** fastapi
**Feature used:** Agent mode
**What happened:** Agent imported `inline_snapshot` in test file without installing the package — ModuleNotFoundError on collection
**What I expected:** Agent to use existing imports or install the package
**Severity:** P1
**Became:** bug_report_1.md (same root cause as Observation 1)

## Observation 3 — What worked
**Feature used:** Agent mode
**What happened:** The actual /health endpoint implementation and test logic were correct — test PASSED once dependencies were manually installed
**Note:** Agent got the functional code right but broke the dev environment getting there

