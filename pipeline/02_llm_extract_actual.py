# Stage 2 (replacement for pipeline/02): real usage metadata, batched, threaded, cached.
import json, time, re, html, sys, duckdb, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types
MODEL=sys.argv[1] if len(sys.argv)>1 else "gemini-3.5-flash-lite"
BATCH=40; WORKERS=4
C=Path("data/llm_cache2"); C.mkdir(parents=True,exist_ok=True)
client=genai.Client()
PROMPT="""You extract book recommendations from Hacker News comments.
For each comment, list every specific, identifiable BOOK the commenter names (not papers, blogs, films, courses, or software).
Return a JSON array of objects: {"comment_id": "<id>", "title": str, "author": str ("" if unknown and not inferable with certainty), "stance": "strong_rec|rec|reference|critical|joke", "why": "<=20 words, paraphrase of the commenter's reason", "quote": "EXACT verbatim substring copied from the comment, <=25 words"}
Stances: strong_rec = enthusiastic ("must read", "changed my life", "best book on X"); rec = positive; reference = neutral mention; critical = negative; joke = sarcastic.
Never invent books. Only use the comment text. Omit comments with no book. Output [] if none.
Comments:
"""
def strip(t): return html.unescape(re.sub(r"<[^>]+>"," ",t.replace("<p>","\n")))
lock=threading.Lock(); usage={"prompt":0,"output":0,"thoughts":0,"calls":0,"errors":0}
def run(bi,batch):
    f=C/f"b{bi:05d}.json"
    if f.exists(): return
    body="".join(f"\n### comment_id: {cid}\n{strip(t)[:2000]}\n" for cid,t in batch)
    for att in range(8):
        try:
            r=client.models.generate_content(model=MODEL,contents=PROMPT+body,
              config=types.GenerateContentConfig(response_mime_type="application/json",temperature=0.1))
            data=json.loads(r.text); u=r.usage_metadata
            with lock:
                usage["prompt"]+=u.prompt_token_count or 0; usage["output"]+=u.candidates_token_count or 0
                usage["thoughts"]+=u.thoughts_token_count or 0; usage["calls"]+=1
            f.write_text(json.dumps({"ids":[c for c,_ in batch],"out":data,"usage":{"p":u.prompt_token_count,"o":u.candidates_token_count,"t":u.thoughts_token_count}}))
            return
        except Exception as e:
            msg=str(e)[:160]
            with lock: usage["errors"]+=1
            print("batch",bi,"attempt",att,msg,flush=True); time.sleep(min(60,5*2**att))
rows=duckdb.connect().execute("select id,text from 'data/candidates.parquet' order by id").fetchall()
batches=[rows[i:i+BATCH] for i in range(0,len(rows),BATCH)]
t=time.time(); print(len(rows),"comments",len(batches),"batches",MODEL,flush=True)
with ThreadPoolExecutor(WORKERS) as ex:
    for i,_ in enumerate(ex.map(lambda a: run(*a), enumerate(batches))):
        if i%25==0: print(i,round(time.time()-t),usage,flush=True)
# assemble with verbatim-quote check
text={str(c):strip(t) for c,t in rows}
out={}; tot={"p":0,"o":0,"t":0}; dropped=0; kept=0; missing=0
norm=lambda s: re.sub(r"\s+"," ",s).strip().lower()
for f in sorted(C.glob("b*.json")):
    d=json.loads(f.read_text())
    for k in tot: tot[k]+=d["usage"][k] or 0
    for cid in d["ids"]: out.setdefault(str(cid),{"books":[]})
    o=d["out"]; o=o.get("books",o.get("results",[])) if isinstance(o,dict) else o
    for b in (o if isinstance(o,list) else []):
        if not isinstance(b,dict): missing+=1; continue
        cid=str(b.get("comment_id","")).strip()
        if cid not in text or not b.get("title"): missing+=1; continue
        q=b.get("quote","")
        if norm(q) and norm(q) not in norm(text[cid]): dropped+=1; b["quote"]=""; b["quote_unverified"]=True
        kept+=1; out[cid]["books"].append({k:b.get(k,"") for k in ["title","author","stance","why","quote"]})
Path("data/extracted_books.json").write_text(json.dumps(out,indent=1))
done=len(list(C.glob("b*.json")))
summary={"model":MODEL,"batches_done":done,"batches_total":len(batches),"comments":len(rows),"book_mentions":kept,"quotes_not_verbatim_blanked":dropped,"bad_ids":missing,"tokens_prompt":tot["p"],"tokens_output":tot["o"],"tokens_thoughts":tot["t"],"wall_secs_this_run":round(time.time()-t),"errors_this_run":usage["errors"]}
Path("../work/stage2_usage.json").write_text(json.dumps(summary,indent=1)); print(summary)
