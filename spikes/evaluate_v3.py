import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from dataset_v3 import DOCS, QUESTIONS

def is_ar(t):
    return any("\u0600" <= c <= "\u06FF" for c in t)

bi = SentenceTransformer("intfloat/multilingual-e5-large")
ce = CrossEncoder("BAAI/bge-reranker-v2-m3")

keys = list(DOCS.keys())
doc_lang = {k: ("ar" if is_ar(DOCS[k]) else "en") for k in keys}
d = bi.encode(["passage: " + DOCS[k] for k in keys])

b1 = b5 = bsame = r1 = rsame = 0

for q, exp in QUESTIONS:
    s = util.cos_sim(bi.encode("query: " + q), d)[0]
    ranked = [keys[j] for j in s.argsort(descending=True)]
    top5 = ranked[:5]
    qlang = "ar" if is_ar(q) else "en"

    b1 += exp == ranked[0]
    b5 += exp in top5
    bsame += doc_lang[ranked[0]] == qlang

    sc = ce.predict([(q, DOCS[k]) for k in top5])
    best = top5[int(np.argmax(sc))]
    r1 += exp == best
    rsame += doc_lang[best] == qlang

n = len(QUESTIONS)
print(f"questions = {n}, all cross-lingual, no translated duplicates\n")
print(f"dense only        R@1={b1/n:.2f}  R@5={b5/n:.2f}  same-lang={bsame/n:.2f}")
print(f"dense + reranker  R@1={r1/n:.2f}              same-lang={rsame/n:.2f}")
