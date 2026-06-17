# Bug Report #1 — Agent mode introduces uninstalled dependencies that break entire test suite collection

**Severity:** P1

**Severity rationale:** The failure is invisible at code review — the imports look valid and the test logic is correct. But every developer who pulls the branch gets a full test suite INTERNALERROR on first run with no actionable error message pointing to the missing package. Workaround requires knowing to pip install two separate unlisted packages.

## Steps to reproduce
1. Open fastapi repo in Cursor Agent mode
2. Prompt: "Add a /health endpoint. Update the app, docs, and tests."
3. Accept all Agent changes
4. Run: `PYTHONPATH=. python3 -m pytest tests/test_application.py::test_health -v`

## Expected
Tests collect and run successfully on first run with no additional setup.

## Actual
Two separate failures block test collection
cat > /Users/anupa/Documents/Anupa/mygitprojects/cursor-quality-lab/bug-reports/bug_report_1.md << 'EOF'
# Bug Report #1 — Agent mode introduces uninstalled dependencies that break entire test suite collection

**Severity:** P1

**Severity rationale:** The failure is invisible at code review — the imports look valid and the test logic is correct. But every developer who pulls the branch gets a full test suite INTERNALERROR on first run with no actionable error message pointing to the missing package. Workaround requires knowing to pip install two separate unlisted packages.

## Steps to reproduce
1. Open fastapi repo in Cursor Agent mode
2. Prompt: "Add a /health endpoint. Update the app, docs, and tests."
3. Accept all Agent changes
4. Run: `PYTHONPATH=. python3 -m pytest tests/test_application.py::test_health -v`

## Expected
Tests collect and run successfully on first run with no additional setup.

## Actual
Two separate failures block test collection entirely:
- `ModuleNotFoundError: No module named 'inline_snapshot'` — Agent added this import to the test file without installing it
- `Unknown config option: timeout` in pytest.ini — Agent added timeout config without installing pytest-timeout, causing INTERNALERROR that kills all test collection

## Customer impact
Any developer cloning a branch with Agent-generated tests gets a broken test suite on first run. No pip install step is suggested, no requirements.txt or pyproject.toml is updated, no error message points to the root cause.

## Root cause pattern
Agent introduces new imports and config options without verifying they are installed or adding them to the project's dependency manifest. This is a systemic pattern — not two isolated bugs but one root cause affecting any Agent-generated test code.

## Suggested engineering scope
Agent should either:
- (a) Only use imports already present in the target test file, or
- (b) Automatically run pip install and update requirements/pyproject.toml as part of the same change set

## Environment
- Cursor version: [your version — check Cursor → About]
- OS: macOS
- Python: 3.14.3
- pytest: 9.0.3
- Repo: github.com/tiangolo/fastapi
