# Cursor VoC Signal Memo — June 2026

**Prepared by:** Anupa Abdul Rahiman  
**Sources:** Reddit r/cursor, Cursor Community Forum, Cursor Changelog  
**Data:** 19 user complaints collected June 1–17 2026  
**Purpose:** Synthesize top user pain points for product and engineering triage  

---

## Top 5 Pain Points — Ranked by Severity × Frequency

---

### #1 — Agent mode causes irreversible file changes with no review step
**Severity:** P0  
**Report count:** 4  
**Pattern:** After a recent Cursor update, Agent mode applies file edits directly to disk with no inline diff, no Accept/Reject controls, and no Undo. In separate reports, repeated Agent edits cause files to be deleted entirely. Users cannot review or roll back changes.  
**User signal:** "Files are modified without user consent." "The file gets deleted — this is a bug in how Cursor does writes." "No red/green diff shown. Changes auto-accepted with no review step."  
**Routing:** Engineering escalation — P0. Data loss and silent file mutation with no recovery path.

---

### #2 — Tab completion broken or silently deletes unrelated code
**Severity:** P0  
**Report count:** 4  
**Pattern:** Tab completion stops working entirely across multiple Cursor versions. Logs show `Error in streaming cpp [not_found]` on every request. In a separate pattern, Tab shows a suggestion but pressing Tab does nothing — or deletes 5–20 unrelated lines below the cursor position.  
**User signal:** "Tab completion stopped working entirely." "I furiously press tab but nothing happens — then it deletes unrelated code." "Codebase indexing stuck on loading forever."  
**Routing:** Engineering escalation — P0. Silent data loss and complete feature failure.

---

### #3 — Cursor crashes on shutdown requiring daily reinstall
**Severity:** P0  
**Report count:** 1  
**Pattern:** Cursor fails to install updates on shutdown, crashes, and uninstalls itself. User must reinstall every day to use the product.  
**User signal:** "Getting failed to install cursor update. This results in cursor crash uninstalling from users system. Needing to install again everyday."  
**Routing:** Engineering escalation — P0. Complete product unavailability for affected users.

---

### #4 — Excessive token consumption in Agent plan mode
**Severity:** P1  
**Report count:** 1  
**Pattern:** A single prompt in plan mode consumed 5 million GPT-5.5 tokens — jumping API usage from 35% to 75%. Adding an MCP server triggered runaway token usage. Same task on Codex used 300k tokens.  
**User signal:** "I definitely think it's a bug. I did not experience this on Codex. That single prompt consumed roughly 5 million tokens."  
**Routing:** Engineering escalation — P1. Potential runaway cost impact for all plan mode + MCP users.

---

### #5 — Context compression silently drops recent edits
**Severity:** P1  
**Report count:** 2  
**Pattern:** Cursor's context compression forgets edits made 2 minutes ago — especially small one-liners. Compression weights by space occupied in conversation, not by recency or importance. No timeline from Cursor support.  
**User signal:** "It is not a bug in the model. It is a context management issue." "The compression weights things by how much space they occupied — almost the opposite of how much they actually matter."  
**Routing:** Product triage — P1. Architectural decision required on compression priority weighting.

---

## Routing Summary

| Pain point | Severity | Count | Routing |
|---|---|---|---|
| Agent file changes — no review/undo | P0 | 4 | Engineering escalation |
| Tab completion broken / deletes code | P0 | 4 | Engineering escalation |
| Cursor crashes — daily reinstall | P0 | 1 | Engineering escalation |
| Excessive token consumption plan mode | P1 | 1 | Engineering escalation |
| Context compression drops recent edits | P1 | 2 | Product triage |

---

## Feedback loop gap — where signal gets lost
Three P0 issues (Agent file deletion, Tab data loss, shutdown crash) have multiple community reports dating back to late 2025 with no public resolution timeline. Signal is reaching the forum but not closing the loop back to users with fix status. Highest-leverage automation opportunity: alert engineering when a P0 complaint pattern appears across 3+ independent reports within a 30-day window.

---

## Signal gaps
- No Discord data collected yet — likely more real-time P0s there
- Changelog fixed items suggest HTTP/2 streaming and Agent checkpoint bugs recently resolved — monitor for regression
- Tab completion issues span multiple Cursor versions suggesting systemic root cause not release-specific
