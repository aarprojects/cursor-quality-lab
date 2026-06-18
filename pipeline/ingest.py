"""
Cursor VoC Signal Ingester — Day 4
Runs in two modes:
  --source reddit   Pull live posts via PRAW (requires API credentials)
  --source csv      Process local voc_raw_data.csv (default, no credentials needed)

Day 6 upgrade: replace keyword classifier with Claude API (LLM-as-judge).

Usage:
    python ingest.py                        # CSV mode (default)
    python ingest.py --source csv           # explicit CSV mode
    python ingest.py --source reddit        # Reddit live pull
"""

import csv
import os
import argparse
from datetime import datetime, timezone

OUTPUT_FILE = "voc_raw_data_reddit.csv"
INPUT_CSV   = "voc_raw_data.csv"


# ── Product area classifier ────────────────────────────────────────────────────
AREA_KEYWORDS = {
    "Tab completion": ["tab", "autocomplete", "completion", "suggestion", "copilot"],
    "Agent mode":     ["agent", "agentic", "compose", "multi-file", "edit mode"],
    "Context window": ["context", "forget", "memory", "compression", "long file"],
    "Performance":    ["slow", "crash", "freeze", "hang", "token", "expensive", "cpu", "ram"],
    "UI":             ["ui", "interface", "button", "layout", "display", "chat"],
}

def classify_area(text: str) -> str:
    t = text.lower()
    for area, keywords in AREA_KEYWORDS.items():
        if any(k in t for k in keywords):
            return area
    return "Other"


# ── Severity classifier (keyword rules — upgraded to LLM on Day 6) ─────────────
def classify_severity(text: str) -> str:
    t = text.lower()
    p0 = ["crash","lost work","data loss","deleted my","unusable","completely broken",
          "every time","100% repro","reinstall","not_found","indexing stuck"]
    p1 = ["wrong","incorrect","broken","not working","doesn't work","stopped working",
          "bug","issue","error","fails","fail","inconsistent","unreliable","forget",
          "token","expensive","slow"]
    p2 = ["annoying","minor","wish","would be nice","workaround","slightly","sometimes"]
    noise = ["how do i","how to","tutorial","docs","anyone else use","recommend","best way"]

    if any(s in t for s in noise):   return "Noise"
    if any(s in t for s in p0):      return "P0"
    if any(s in t for s in p1):      return "P1"
    if any(s in t for s in p2):      return "P2"
    return "P2"


# ── CSV mode ───────────────────────────────────────────────────────────────────
def run_csv(input_file: str) -> list[dict]:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    rows = []
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            combined = f"{row['description']} {row.get('notes', '')}"
            # Re-run classifier so we can compare vs manual tags on Day 6
            auto_severity = classify_severity(combined)
            auto_area     = classify_area(combined)

            rows.append({
                "source":           row["source"],
                "title":            row["description"],
                "body_snippet":     row.get("notes", "")[:200],
                "product_area":     auto_area,
                "severity_tag":     auto_severity,
                "manual_severity":  row.get("severity", ""),   # keep original for Day 6 comparison
                "manual_area":      row.get("product_area", ""),
                "date":             row["date"],
                "url":              "",
                "score":            "",
                "num_comments":     "",
            })

    print(f"  {len(rows)} rows loaded from {input_file}")
    return rows


# ── Reddit mode ────────────────────────────────────────────────────────────────
def run_reddit() -> list[dict]:
    try:
        import praw
    except ImportError:
        raise ImportError("pip install praw")

    REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
    REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "cursor-voc-tracker/1.0 by aarprojects")

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    SUBREDDITS   = ["cursor", "ChatGPTCoding"]
    SEARCH_QUERY = "cursor bug OR cursor issue OR cursor broken OR cursor not working"

    rows = []
    for subreddit_name in SUBREDDITS:
        print(f"\n  Pulling from r/{subreddit_name}...")
        sub   = reddit.subreddit(subreddit_name)
        posts = sub.search(SEARCH_QUERY, sort="new", time_filter="month", limit=100)

        count = 0
        for post in posts:
            title    = post.title.strip()
            body     = (post.selftext or "").strip()
            combined = f"{title} {body}"

            if len(combined) < 30 or body in ("[deleted]", "[removed]"):
                continue

            rows.append({
                "source":          f"r/{subreddit_name}",
                "title":           title,
                "body_snippet":    body[:200].replace("\n", " "),
                "product_area":    classify_area(combined),
                "severity_tag":    classify_severity(combined),
                "manual_severity": "",
                "manual_area":     "",
                "date":            datetime.fromtimestamp(
                                       post.created_utc, tz=timezone.utc
                                   ).strftime("%Y-%m-%d"),
                "url":             f"https://reddit.com{post.permalink}",
                "score":           post.score,
                "num_comments":    post.num_comments,
            })
            count += 1

        print(f"  {count} posts collected from r/{subreddit_name}")

    return rows


# ── Output + summary ───────────────────────────────────────────────────────────
def write_and_summarize(rows: list[dict]):
    if not rows:
        print("No data to write.")
        return

    severity_order = {"P0": 0, "P1": 1, "P2": 2, "Noise": 3}
    rows.sort(key=lambda r: severity_order.get(r["severity_tag"], 4))

    fieldnames = [
        "source", "title", "body_snippet",
        "product_area", "severity_tag",
        "manual_severity", "manual_area",
        "date", "url", "score", "num_comments",
    ]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'─'*52}")
    print(f"Output: {OUTPUT_FILE}  ({len(rows)} rows)\n")

    print("Severity breakdown:")
    for sev in ["P0", "P1", "P2", "Noise"]:
        n   = sum(1 for r in rows if r["severity_tag"] == sev)
        bar = "█" * n
        print(f"  {sev:<6} {n:>3}  {bar}")

    print("\nProduct area breakdown:")
    areas = {}
    for r in rows:
        areas[r["product_area"]] = areas.get(r["product_area"], 0) + 1
    for area, n in sorted(areas.items(), key=lambda x: -x[1]):
        print(f"  {area:<22} {n}")

    print("\nTop P0s:")
    for r in [r for r in rows if r["severity_tag"] == "P0"][:5]:
        print(f"  [{r['date']}]  {r['title'][:75]}")

    # Day 6 prep: flag mismatches between auto and manual classification
    mismatches = [
        r for r in rows
        if r["manual_severity"] and r["severity_tag"] != r["manual_severity"]
    ]
    if mismatches:
        print(f"\nClassifier mismatches vs manual tags ({len(mismatches)} rows):")
        for r in mismatches:
            print(f"  auto={r['severity_tag']} manual={r['manual_severity']}  {r['title'][:60]}")
        print("  → Review these on Day 6 when upgrading to LLM-as-judge")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cursor VoC ingester")
    parser.add_argument(
        "--source",
        choices=["csv", "reddit"],
        default="csv",
        help="Data source: 'csv' (default) or 'reddit'",
    )
    args = parser.parse_args()

    print(f"\nCursor VoC Ingester — source: {args.source}")
    print("─" * 52)

    if args.source == "reddit":
        rows = run_reddit()
    else:
        rows = run_csv(INPUT_CSV)

    write_and_summarize(rows)
