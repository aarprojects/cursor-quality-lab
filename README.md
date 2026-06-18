# Cursor Quality Lab

> An open-source product quality framework for AI-native developer tools — featuring an automated VoC signal pipeline, LLM-as-judge bug classification, and a structured bug report portfolio built through deep product immersion.

[![Pipeline](https://img.shields.io/badge/pipeline-passing-brightgreen)](https://github.com/aarprojects/cursor-quality-lab/actions)
[![Classifier](https://img.shields.io/badge/classifier-LLM--as--judge-blue)](pipeline/ingest.py)
[![Issues Triaged](https://img.shields.io/badge/issues%20triaged-13-orange)](pipeline/triage_output.json)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## What this is

Most quality programs stop at bug reporting. This one doesn't.

This project explores what a **Product Quality Engineer** role looks like when built natively on AI — replacing manual triage spreadsheets with an automated pipeline that ingests community signal, classifies severity using an LLM, routes issues to the right team, and alerts on P0s before they compound.

It covers three things:

- **Deep product testing** — hands-on Cursor usage to surface real bugs, written as engineer-ready reports
- **VoC signal intelligence** — community pain points mined, categorized, and synthesized into actionable product signal
- **Automated triage pipeline** — from keyword rules to LLM-as-judge classification, with human-in-the-loop for low-confidence items

---

## Project structurecat > ~/Documents/Anupa/mygitprojects/cursor-quality-lab/README.md << 'EOF'
# Cursor Quality Lab

> An open-source product quality framework for AI-native developer tools — featuring an automated VoC signal pipeline, LLM-as-judge bug classification, and a structured bug report portfolio built through deep product immersion.

[![Pipeline](https://img.shields.io/badge/pipeline-passing-brightgreen)](https://github.com/aarprojects/cursor-quality-lab/actions)
[![Classifier](https://img.shields.io/badge/classifier-LLM--as--judge-blue)](pipeline/ingest.py)
[![Issues Triaged](https://img.shields.io/badge/issues%20triaged-13-orange)](pipeline/triage_output.json)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## What this is

Most quality programs stop at bug reporting. This one doesn't.

This project explores what a **Product Quality Engineer** role looks like when built natively on AI — replacing manual triage spreadsheets with an automated pipeline that ingests community signal, classifies severity using an LLM, routes issues to the right team, and alerts on P0s before they compound.

It covers three things:

- **Deep product testing** — hands-on Cursor usage to surface real bugs, written as engineer-ready reports
- **VoC signal intelligence** — community pain points mined, categorized, and synthesized into actionable product signal
- **Automated triage pipeline** — from keyword rules to LLM-as-judge classification, with human-in-the-loop for low-confidence items

---

## Project structure
cursor-quality-lab/

│

├── bug-reports/                  # Hands-on product testing

│   ├── bug_report_1.md           # Agent mode — P0 file write regression

│   ├── bug_report_2.md           # Tab completion — P0 indexing failure

│   └── bug_report_3.md           # Context window — P1 compression bug

│

├── voc/                          # Voice of the Customer

│   └── voc_memo.md               # Top 5 pain points — PM-ready weekly signal

│

├── pipeline/                     # Automated triage infrastructure

│   ├── ingest.py                 # LLM-as-judge classifier + routing engine

│   ├── voc_raw_data.csv          # 19 community signals, manually tagged

│   ├── voc_raw_data_reddit.csv   # Classified + routed output, P0 first

│   ├── triage_output.json        # 13 triaged P0/P1 issues with reasoning

│   ├── human_review_queue.json   # Low-confidence items for human review

│   └── gap_analysis.md           # Where the feedback loop breaks

│

├── .github/

│   └── workflows/

│       └── voc_pipeline.yml      # Daily cron + P0 Slack alert

│

└── notes/                        # Raw product observations

---

## Bug portfolio

Three engineer-ready reports from direct product testing. Each includes severity rationale, exact reproduction steps, customer impact assessment, workaround availability, and an engineering scope hypothesis.

| # | Product area | Severity | Summary |
|---|---|---|---|
| [1](bug-reports/bug_report_1.md) | Agent mode | **P0** | File changes applied to disk with no diff UI — no Keep/Undo controls, data loss risk |
| [2](bug-reports/bug_report_2.md) | Tab completion | **P0** | Indexing hangs silently — every request returns `[not_found]`, Tab non-functional |
| [3](bug-reports/bug_report_3.md) | Context window | **P1** | Compression discards edits from 2 minutes ago — recency not weighted in compression algorithm |

**What separates these from standard bug reports:** each includes a written severity rationale — not just what broke, but *why this severity and not one lower*, with specific customer impact and workaround analysis.

---

## VoC signal pipeline

### Architecture
Community signal                     Sources: Reddit, Cursor Forum, Changelog

│

▼

ingest.py                          Pulls, deduplicates, classifies

│

├── LLM-as-judge             claude-haiku-4-5 → severity + product area

│   └── human_review_queue   Low-confidence → flagged for human review

│

├── Routing engine           P0 → engineering_escalation

│                            P1 (3+ reports) → engineering_escalation

│                            P1 → product_triage

│                            P2 → backlog

│                            Noise → close

│

└── Outputs

├── triage_output.json   Escalation brief for PM / EM

└── voc_raw_data_reddit.csv

│

▼

GitHub Actions         Daily 9am UTC cron

│

└── P0 detected → Slack alert 🚨

### Classifier evolution

| Stage | Classifier | Accuracy vs manual tags | Notes |
|---|---|---|---|
| v1 | Keyword rules | 42% (8/19) | Fast, free, but misses descriptive phrasing |
| v2 | Claude API (LLM-as-judge) | Run to measure | Handles nuance, confidence scoring, reasoning |

### Run it locally

```bash
git clone https://github.com/aarprojects/cursor-quality-lab.git
cd cursor-quality-lab/pipeline

pip install anthropic rapidfuzz
export ANTHROPIC_API_KEY=your_key

python ingest.py                   # LLM classifier, CSV source (default)
python ingest.py --no-llm          # keyword rules only
python ingest.py --source reddit   # live Reddit pull (requires credentials)
```

### Outputs explained

**`triage_output.json`** — the escalation brief. Every P0 and P1, with severity, routing decision, report_count, sample quotes, and LLM reasoning.

**`human_review_queue.json`** — low-confidence classifications flagged for human review. Humans stay in the loop by design.

---

## Gap analysis

| Gap | Impact | Fix |
|---|---|---|
| Reddit → nowhere | P1 bugs with 80+ upvotes have no path to engineering | Route high-engagement posts by score threshold |
| Forum → slow triage | Oldest unresolved reports 8+ months old | SLA clock at ingestion time |
| Duplicates inflate noise | Same bug looks like separate reports | Fuzzy dedup + report_count amplifier ✅ (built) |
| Changelog fixes are silent | Users who filed bugs never learn they're fixed | Cross-reference fixed issues to original threads |

Full analysis: [`pipeline/gap_analysis.md`](pipeline/gap_analysis.md)

---

## GitHub Actions

```yaml
on:
  schedule:
    - cron: "0 9 * * *"   # daily at 9am UTC
  workflow_dispatch:        # manual trigger anytime
```

On each run: classifies signal → deduplicates → routes → fires Slack on any P0 detection.

To enable: add `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL` as repository secrets.

---

## VoC memo — top 5 pain points

Ranked by severity × frequency from 19 community signals:

1. **Agent mode — file integrity** — P0 — engineering escalation
2. **Tab completion — indexing failure** — P0 — engineering escalation
3. **Agent mode — CI reliability** — P1 — product triage
4. **Context window — compression** — P1 — product triage
5. **Performance — token explosion** — P1 — product triage

Full memo: [`voc/voc_memo.md`](voc/voc_memo.md)

---

## Numbers

| Metric | Value |
|---|---|
| Community signals analyzed | 19 |
| P0s detected | 5 |
| Issues triaged (P0 + P1) | 13 |
| Engineering escalations | 8 |
| Keyword classifier accuracy | 42% |
| Pipeline cadence | Daily (automated) |

---

*Built by [Anupa Abdul Rahiman](https://github.com/aarprojects) — Staff QE / Automation Tech Lead*
*Previously: Block/Square, eBay*
