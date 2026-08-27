import sys
sys.path.insert(0, "spikes")

from dataset_v3 import DOCS, QUESTIONS
from nexa.rag.retriever import Retriever

r = Retriever()
r.index(DOCS)

hits = 0
for q, expected in QUESTIONS:
    top = r.search(q)[0]
    ok = top.doc_id == expected
    hits += ok
    if not ok:
        print(f"MISS: {q[:40]:<42} want={expected:<14} got={top.doc_id}")

n = len(QUESTIONS)
print(f"\nRecall@1 = {hits}/{n} = {hits/n:.2f}")
