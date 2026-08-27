import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from dataset_v2 import DOCS, QUESTIONS

bi = SentenceTransformer("intfloat/multilingual-e5-large")
ce = CrossEncoder("BAAI/bge-reranker-v2-m3")
keys = list(DOCS.keys())
d = bi.encode(["passage: " + DOCS[k] for k in keys])

for i in list(range(1, len(QUESTIONS), 2))[:4]:
    q, exp = QUESTIONS[i]
    s = util.cos_sim(bi.encode("query: " + q), d)[0]
    top5 = [keys[j] for j in s.argsort(descending=True)[:5]]
    sc = ce.predict([(q, DOCS[k]) for k in top5])
    print(f"\nQ: {q}   (want: {exp})")
    for k, v in sorted(zip(top5, sc), key=lambda x: -x[1]):
        mark = " <-- WANT" if k == exp else ""
        print(f"   {v:7.3f}  {k}{mark}")
