"""
Cursor VoC Signal Aggregator — Day 4
Ingests Reddit r/cursor posts and classifies by severity using keyword rules.
Day 6: upgrade classifier to LLM-as-judge (Claude API)
"""

import praw
import csv
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="cursor-quality-lab:v1.0 (by /u/YOUR_REDDIT_USERNAME)"
)

SEARCH_TERMS = [
    "bug", "broken", "not working", "crash",
    "context lost", "tab completion", "agent mode"
]

PRODUCT_AREA_KEYWORDS = {
    "Tab completion": ["tab", "completion", "autocomplete", "suggestion", "not_found"],
    "Agent": ["agent", "dispose", "checkpoint", "edit file", "delete file"],
    "Context window": ["context", "compression", "forgets", "lost context"],
    "Performance": ["slow", "crash", "token", "api usage", "hang", "freeze"],
    "UI": ["ui", "ux", "layout", "chat", "interface", "button"],
    "Multi-file": ["multi-file", "multifile", "rename", "refactor", "across files"],
}

SEVERITY_KEYWORDS = {
    "P0": ["crash", "delete", "lost work", "unusable", "data loss",
           "reinstall", "not working", "broken entirely", "every time"],
    "P1": ["wrong", "incorrect", "slow", "inconsistent", "sometimes",
           "intermittent", "worse", "hallucinate", "context lost"],
    "P2": ["annoying", "minor", "workaround", "confusing", "wish",
           "would be nice", "ux", "button"],
}


def classify_product_area(text: str) -> str:
    text_lower = text.lower()
    for area, keywords in PRODUCT_AREA_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return area
    return "Other"


def classify_severity(text: str) -> str:
    text_lower = text.lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return severity
    return "Noise"


def route(severity: str) -> str:
    return {
        "P0": "engineering_escalation",
        "P1": "product_triage",
        "P2": "backlog",
        "Noise": "close",
    }.get(severity, "close")


def fetch_posts(limit: int = 25) -> list:
    posts = []
    seen_ids = set()

    for term in SEARCH_TERMS:
        print(f"Searching r/cursor for: '{term}'...")
        try:
            results = reddit.subreddit("cursor").search(
                term, sort="new", limit=limit
            )
            for post in results:
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)
                text = f"{post.title} {post.selftext}"
                severity = classify_severity(text)
                product_area = classify_product_area(text)
                posts.append({
                    "source": "reddit",
                    "date": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d"),
                    "description": post.title[:120],
                    "product_area": product_area,
                    "severity": severity,
                    "report_count": 1,
                    "routing": route(severity),
                    "url": f"https://reddit.com{post.permalink}",
                })
        except Exception as e:
            print(f"Error fetching '{term}': {e}")

    return posts


def save_to_csv(posts: list, path: str = "pipeline/triage_output.csv"):
    if not posts:
        print("No posts to save.")
        return
    fieldnames = ["source", "date", "description", "product_area",
                  "severity", "report_count", "routing", "url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(posts)
    print(f"Saved {len(posts)} posts to {path}")


if __name__ == "__main__":
    posts = fetch_posts(limit=25)
    save_to_csv(posts)
    p0s = [p for p in posts if p["severity"] == "P0"]
    p1s = [p for p in posts if p["severity"] == "P1"]
    noise = [p for p in posts if p["severity"] == "Noise"]
    print(f"\nSummary: {len(posts)} posts | P0: {len(p0s)} | P1: {len(p1s)} | Noise: {len(noise)}")
    if p0s:
        print("\nP0 escalations:")
        for p in p0s:
            print(f"  [{p['product_area']}] {p['description'][:80]}")
