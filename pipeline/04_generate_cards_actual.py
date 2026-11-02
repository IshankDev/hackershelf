import json,time,sys,importlib.util,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types
spec=importlib.util.spec_from_file_location("g","pipeline/04_generate_cards.py"); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
MODEL="gemini-3.5-flash-lite"; client=genai.Client()
books=json.load(open("data/filtered_books.json")); C=Path("data/card_cache"); C.mkdir(exist_ok=True)
tot={"p":0,"o":0,"t":0,"calls":0,"fallbacks":0}; lock=threading.Lock()
def one(item):
    k,b=item; f=C/f"{k}.json"
    if f.exists(): return k,json.loads(f.read_text())
    ms="\n".join(f"- {m['by']} ({m['stance']}): {m['why']} | \"{m['quote']}\"" for m in b["mentions"][:10])
    p=g.CARD_PROMPT_TEMPLATE.format(title=b["title"],author=b["author"],mentions=ms)
    for a in range(8):
        try:
            r=client.models.generate_content(model=MODEL,contents=p,config=types.GenerateContentConfig(response_mime_type="application/json",temperature=0.3))
            d=json.loads(r.text); d=d[0] if isinstance(d,list) else d; u=r.usage_metadata
            with lock: tot["p"]+=u.prompt_token_count or 0; tot["o"]+=u.candidates_token_count or 0; tot["t"]+=u.thoughts_token_count or 0; tot["calls"]+=1
            f.write_text(json.dumps(d)); return k,d
        except Exception as e: print(k,a,str(e)[:120],flush=True); time.sleep(min(60,5*2**a))
    with lock: tot["fallbacks"]+=1
    return k,{"summary":"","why_hn":"","level":"intermediate","kind":"other","topics":b.get("subjects",[])[:3]}
t=time.time(); final={}
with ThreadPoolExecutor(4) as ex:
    for k,card in ex.map(one,books.items()):
        b=books[k]; final[k]={**b,**card,"categories":g.assign_categories({**b,**card})}
json.dump(final,open("data/final_books.json","w"),indent=2)
tot["secs"]=round(time.time()-t); tot["books"]=len(final); json.dump(tot,open("../work/stage4_usage.json","w")); print(tot)
