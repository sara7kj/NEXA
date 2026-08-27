import numpy as np
from sentence_transformers import SentenceTransformer, util
from dataset_v2 import DOCS, QUESTIONS

def is_ar(t):
    return any("\u0600" <= c <= "\u06FF" for c in t)

model = SentenceTransformer("intfloat/multilingual-e5-large")
keys = list(DOCS.keys())
doc_lang = {k: ("ar" if is_ar(DOCS[k]) else "en") for k in keys}

d = np.array(model.encode(["passage: " + DOCS[k] for k in keys]), dtype=float)
q = np.array(model.encode(["query: " + t for t, _ in QUESTIONS]), dtype=float)

train = list(range(0, len(QUESTIONS), 2))   # even -> compute centering
test  = list(range(1, len(QUESTIONS), 2))   # odd  -> evaluate

def run(doc_emb, q_emb, label):
    r1 = r5 = same = 0
    for i in test:
        exp = QUESTIONS[i][1]
        s = util.cos_sim(q_emb[i], doc_emb)[0]
        ranked = [keys[j] for j in s.argsort(descending=True)]
        r1 += exp == ranked[0]
        r5 += exp in ranked[:5]
        same += doc_lang[ranked[0]] == ("ar" if is_ar(QUESTIONS[i][0]) else "en")
    n = len(test)
    print(f"{label:<26} R@1={r1/n:.2f}  R@5={r5/n:.2f}  same-lang={same/n:.2f}")

run(d, q, "baseline")

dc, qc = d.copy(), q.copy()
for lang in ("ar", "en"):
    di = [i for i, k in enumerate(keys) if doc_lang[k] == lang]
    dc[di] -= dc[di].mean(axis=0)
    qi = [i for i in train if ("ar" if is_ar(QUESTIONS[i][0]) else "en") == lang]
    mu = qc[qi].mean(axis=0)
    for i in range(len(QUESTIONS)):
        if ("ar" if is_ar(QUESTIONS[i][0]) else "en") == lang:
            qc[i] -= mu
run(dc, qc, "centering (held-out)")

print(f"\ntest set = {len(test)} questions, all cross-lingual")
