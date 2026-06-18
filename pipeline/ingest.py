"""
Cursor VoC Signal Ingester — Day 6
Upgrades Day 5 keyword classifier -> Claude API (LLM-as-judge).
Adds: human_review queue for low-confidence results, accuracy report vs manual tags.

Modes:
    python ingest.py                     # CSV + LLM classifier (default)
    python ingest.py --source csv        # explicit CSV mode
    python ingest.py --source reddit     # requires Reddit API credentials
    python ingest.py --no-llm            # fall back to keyword rules

Requirements:
    pip install anthropic rapidfuzz
    export ANTHROPIC_API_KEY=your_key
"""

import csv, os, json, argparse, time
from datetime import datetime, timezone
from rapidfuzz import fuzz
import anthropic

OUTPUT_CSV      = "voc_raw_data_reddit.csv"
OUTPUT_JSON     = "triage_output.json"
OUTPUT_HUMAN    = "human_review_queue.json"
INPUT_CSV       = "voc_raw_data.csv"
DEDUP_THRESHOLD = 75
ESCALATION_COUNT= 3

AREA_KEYWORDS = {
    "Tab completion": ["tab","autocomplete","completion","suggestion","copilot"],
    "Agent mode":     ["agent","agentic","compose","multi-file","edit mode"],
    "Context window": ["context","forget","memory","compression","long file"],
    "Performance":    ["slow","crash","freeze","hang","token","expensive","cpu","ram"],
    "UI":             ["ui","interface","button","layout","display","chat"],
}

def keyword_area(text):
    t = text.lower()
    for area, kw in AREA_KEYWORDS.items():
        if any(k in t for k in kw): return area
    return "Other"

def keyword_severity(text):
    t = text.lower()
    p0    = ["crash","lost work","data loss","deleted my","unusable","completely broken","every time","100% repro","reinstall","not_found","indexing stuck"]
    p1    = ["wrong","incorrect","broken","not working","stopped working","bug","issue","error","fails","fail","inconsistent","unreliable","forget","token","expensive","slow"]
    p2    = ["annoying","minor","wish","would be nice","workaround","slightly","sometimes"]
    noise = ["how do i","how to","tutorial","docs","anyone else use","recommend","best way"]
    if any(s in t for s in noise): return "Noise"
    if any(s in t for s in p0):    return "P0"
    if any(s in t for s in p1):    return "P1"
    if any(s in t for s in p2):    return "P2"
    return "P2"

SYSTEM_PROMPT = """You are a senior Product Quality Engineer at Cursor, an AI code editor.
Classify user-reported complaints by severity and product area.

Severity:
- P0: blocks work entirely, data loss risk, crash, 100% reproducible failure
- P1: significant degradation, broken feature, no good workaround
- P2: annoying but workaround exists, minor UX issue
- Noise: question, feature request, praise, or unclear

Product areas: Tab completion, Agent mode, Context window, Performance, UI, Other

Respond ONLY with a JSON object. No preamble, no markdown.
{"severity":"P0|P1|P2|Noise","product_area":"...","routing":"engineering_escalation|product_triage|backlog|close","confidence":"high|medium|low","reasoning":"one sentence"}"""

def llm_classify(client, title, body):
    text = f"Title: {title}\nDescription: {body[:300]}" if body else f"Title: {title}"
    try:
        response = client.messages.create(
            model="claude-haiku-4-5", max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role":"user","content":text}]
        )
        raw = response.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        combined = f"{title} {body}"
        return {"severity":keyword_severity(combined),"product_area":keyword_area(combined),
                "routing":"product_triage","confidence":"low","reasoning":f"fallback: {e}"}

def route(severity, report_count):
    if severity == "P0": return "engineering_escalation"
    if severity == "P1" and report_count >= ESCALATION_COUNT: return "engineering_escalation"
    if severity == "P1": return "product_triage"
    if severity == "P2": return "backlog"
    return "close"

def deduplicate(rows):
    clusters = []
    for row in rows:
        matched = False
        for c in clusters:
            if fuzz.token_sort_ratio(row["title"], c["title"]) >= DEDUP_THRESHOLD:
                c["report_count"] += 1
                if row["body_snippet"] and row["body_snippet"] not in c["sample_quotes"] and len(c["sample_quotes"]) < 3:
                    c["sample_quotes"].append(row["body_snippet"])
                if row["date"] < c["date"]: c["date"] = row["date"]
                matched = True; break
        if not matched:
            new = dict(row)
            new["report_count"]  = 1
            new["sample_quotes"] = [row["body_snippet"]] if row["body_snippet"] else []
            clusters.append(new)
    return clusters

def run_csv(input_file):
    rows = []
    with open(input_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({"source":row["source"],"title":row["description"],
                "body_snippet":row.get("notes","")[:200],
                "manual_severity":row.get("severity",""),"manual_area":row.get("product_area",""),
                "date":row["date"],"url":"","score":"","num_comments":""})
    print(f"  {len(rows)} rows loaded from {input_file}")
    return rows

def run_reddit():
    import praw
    reddit = praw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID",""),
                         client_secret=os.getenv("REDDIT_CLIENT_SECRET",""),
                         user_agent=os.getenv("REDDIT_USER_AGENT","cursor-voc-tracker/1.0"))
    rows = []
    for sub in ["cursor","ChatGPTCoding"]:
        for post in reddit.subreddit(sub).search("cursor bug OR issue OR broken",sort="new",time_filter="month",limit=100):
            title,body = post.title.strip(),(post.selftext or "").strip()
            if len(f"{title}{body}") < 30 or body in ("[deleted]","[removed]"): continue
            rows.append({"source":f"r/{sub}","title":title,"body_snippet":body[:200].replace("\n"," "),
                "manual_severity":"","manual_area":"",
                "date":datetime.fromtimestamp(post.created_utc,tz=timezone.utc).strftime("%Y-%m-%d"),
                "url":f"https://reddit.com{post.permalink}","score":post.score,"num_comments":post.num_comments})
    return rows

def write_outputs(rows):
    rows.sort(key=lambda r: {"P0":0,"P1":1,"P2":2,"Noise":3}.get(r["severity_tag"],4))
    with open(OUTPUT_CSV,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f,fieldnames=["source","title","body_snippet","product_area","severity_tag",
            "manual_severity","manual_area","date","url","score","num_comments","report_count","routing",
            "llm_confidence","llm_reasoning"],extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"  CSV  -> {OUTPUT_CSV} ({len(rows)} rows)")

    triage = [{"issue":r["title"],"severity":r["severity_tag"],"routing":r["routing"],
               "report_count":r.get("report_count",1),"product_area":r["product_area"],
               "sample_quotes":r.get("sample_quotes",[r.get("body_snippet","")]),"confidence":r.get("llm_confidence",""),
               "reasoning":r.get("llm_reasoning",""),"date":r["date"]}
              for r in rows if r.get("routing") in ("engineering_escalation","product_triage")]
    with open(OUTPUT_JSON,"w",encoding="utf-8") as f: json.dump(triage,f,indent=2)
    print(f"  JSON -> {OUTPUT_JSON} ({len(triage)} triaged issues)")

    human = [r for r in rows if r.get("llm_confidence") == "low"]
    with open(OUTPUT_HUMAN,"w",encoding="utf-8") as f:
        json.dump([{"issue":r["title"],"auto_severity":r["severity_tag"],
                    "reasoning":r.get("llm_reasoning",""),"date":r["date"]} for r in human],f,indent=2)
    print(f"  JSON -> {OUTPUT_HUMAN} ({len(human)} items need human review)")

def print_summary(rows):
    print(f"\n{'─'*54}")
    for sev in ["P0","P1","P2","Noise"]:
        n = sum(1 for r in rows if r["severity_tag"]==sev)
        print(f"  {sev:<6} {n:>3}  {'█'*n}")
    print()
    for dest in ["engineering_escalation","product_triage","backlog","close"]:
        n = sum(1 for r in rows if r.get("routing")==dest)
        print(f"  {dest:<28} {n}")
    human_count = sum(1 for r in rows if r.get("llm_confidence")=="low")
    if human_count: print(f"\n  -> {human_count} items flagged for human review")

def accuracy_report(rows):
    tagged = [r for r in rows if r.get("manual_severity")]
    if not tagged: return
    correct = sum(1 for r in tagged if r["severity_tag"]==r["manual_severity"])
    pct = round(correct/len(tagged)*100)
    print(f"\nClassifier accuracy: {correct}/{len(tagged)} = {pct}%")
    for r in [r for r in tagged if r["severity_tag"]!=r["manual_severity"]]:
        print(f"  auto={r['severity_tag']} manual={r['manual_severity']}  {r['title'][:55]}")
        print(f"    {r.get('llm_reasoning','')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["csv","reddit"], default="csv")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    use_llm = not args.no_llm
    api_key = os.getenv("ANTHROPIC_API_KEY","")
    if use_llm and not api_key:
        print("Warning: ANTHROPIC_API_KEY not set — falling back to keyword classifier")
        use_llm = False

    print(f"\nCursor VoC Ingester — source: {args.source} | classifier: {'LLM' if use_llm else 'keyword rules'}")
    print("─"*54)

    rows = run_reddit() if args.source=="reddit" else run_csv(INPUT_CSV)
    client = anthropic.Anthropic(api_key=api_key) if use_llm else None

    print(f"\n  Classifying {len(rows)} rows...")
    for i,row in enumerate(rows):
        if use_llm:
            result = llm_classify(client, row["title"], row.get("body_snippet",""))
            time.sleep(0.3)
        else:
            combined = f"{row['title']} {row.get('body_snippet','')}"
            result = {"severity":keyword_severity(combined),"product_area":keyword_area(combined),
                      "routing":"product_triage","confidence":"high","reasoning":"keyword classifier"}
        row["severity_tag"]   = result.get("severity","P2")
        row["product_area"]   = result.get("product_area","Other")
        row["llm_confidence"] = result.get("confidence","high")
        row["llm_reasoning"]  = result.get("reasoning","")
        if (i+1) % 5 == 0: print(f"    {i+1}/{len(rows)} classified...")

    before = len(rows)
    rows = deduplicate(rows)
    print(f"\n  Deduplication: {before} -> {len(rows)} unique ({before-len(rows)} merged)")

    for r in rows: r["routing"] = route(r["severity_tag"], r.get("report_count",1))

    write_outputs(rows)
    print_summary(rows)
    accuracy_report(rows)
