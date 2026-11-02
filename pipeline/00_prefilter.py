# Stage 1b: strong-signal pre-filter over raw HN monthly parquet (2024-01..2026-08)
import duckdb, sys, time
t=time.time()
c=duckdb.connect()
LINK=r"(amazon\.[a-z.]+/([^ ]*/)?(dp|gp/product)/|goodreads\.com/book/show/|openlibrary\.org/(works|books)/|bookshop\.org/|isbn[- ]?(1[03])?:?\s*[0-9][0-9-]{8,16}|oreilly\.com/library/view/|manning\.com/books/|pragprog\.com/titles/|nostarch\.com/)"
PHR=r"(highly recommend[^.]{0,80}\b(book|read)|recommend[^.]{0,60}\bbook|\bmust[- ]read\b|\b(great|excellent|fantastic|best|favou?rite|amazing|wonderful) book\b|\bbook (called|titled|by)\b|\bread(ing)? [^.,;]{2,60} by [A-Z][a-z]+|\bchanged (my|how i)[^.]{0,40}\b(book|read)|\bbooks? i (recommend|always recommend)|worth (a|the) read)"
q=f"""
COPY (
 SELECT id, "by", time, text, parent, year(time) AS year, month(time) AS month FROM (
  SELECT id,"by",time,text,parent, regexp_replace(text,'<[^>]+>','','g') AS plain
  FROM read_parquet('raw/*.parquet')
  WHERE type=2 AND deleted=0 AND dead=0 AND text IS NOT NULL AND "by" IS NOT NULL)
 WHERE length(plain)>=100 AND (regexp_matches(text,'{LINK}','i') OR regexp_matches(plain,'{PHR}','i'))
) TO 'work/candidates_strong.parquet' (FORMAT PARQUET)"""
c.execute(q)
n=c.execute("select count(*), sum(length(text)), count(distinct \"by\") from 'work/candidates_strong.parquet'").fetchall()
tot=c.execute("select count(*) from read_parquet('raw/*.parquet') where type=2").fetchall()
print("all comments",tot,"strong candidates,chars,users",n,"secs",round(time.time()-t))
