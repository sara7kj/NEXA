import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from dataset_v2 import DOCS, QUESTIONS

def is_ar(t):
    return any("\u0600" <= c <= "\u06FF" for c in t)

bi = SentenceTransformer("intfloat/multilingual-e5-large")
ce = CrossEncoder("BAAI/bge-reranker-v2-m3")

keys = list(DOCS.keys())
doc_lang = {k: ("ar" if is_ar(DOCS[k]) else "en") for k in keys}
d = bi.encode(["passage: " + DOCS[k] for k in keys])

test = list(range(1, len(QUESTIONS), 2))
base_r1 = rr_r1 = rr_same = 0

for i in test:
    q, exp = QUESTIONS[i]
    s = util.cos_sim(bi.encode("query: " + q), d)[0]
    top5 = [keys[j] for j in s.argsort(descending=True)[:5]]
    base_r1 += exp == top5[0]

    scores = ce.predict([(q, DOCS[k]) for k in top5])
    best = top5[int(np.argmax(scores))]
    rr_r1 += exp == best
    rr_same += doc_lang[best] == ("ar" if is_ar(q) else "en")

n = len(test)
print(f"dense only        R@1={base_r1/n:.2f}")
print(f"dense + reranker  R@1={rr_r1/n:.2f}   same-lang={rr_same/n:.2f}")
