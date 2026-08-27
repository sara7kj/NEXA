import numpy as np
from sentence_transformers import SentenceTransformer, util
from dataset import DOCS, QUESTIONS

def is_ar(t):
    return any("\u0600" <= c <= "\u06FF" for c in t)

model = SentenceTransformer("intfloat/multilingual-e5-large")
keys = list(DOCS.keys())
doc_lang = {k: ("ar" if is_ar(DOCS[k]) else "en") for k in keys}

def score(doc_emb, q_embs, label):
    r1 = same = 0
    for (q, expected), q_emb in zip(QUESTIONS, q_embs):
        s = util.cos_sim(q_emb, doc_emb)[0]
        top1 = keys[int(s.argmax())]
        r1 += expected == top1
        same += doc_lang[top1] == ("ar" if is_ar(q) else "en")
    n = len(QUESTIONS)
    print(f"{label:<22} Recall@1={r1/n:.2f}   same-lang={same/n:.2f}")

# 1. baseline
d1 = model.encode(["passage: " + DOCS[k] for k in keys])
q1 = model.encode(["query: " + q for q, _ in QUESTIONS])
score(d1, q1, "1. baseline")

# 2. no prefixes
d2 = model.encode([DOCS[k] for k in keys])
q2 = model.encode([q for q, _ in QUESTIONS])
score(d2, q2, "2. no prefixes")

# 3. language mean centering
d3 = np.array(d1, dtype=float)
for lang in ("ar", "en"):
    idx = [i for i, k in enumerate(keys) if doc_lang[k] == lang]
    d3[idx] -= d3[idx].mean(axis=0)
q3 = np.array(q1, dtype=float)
for lang in ("ar", "en"):
    idx = [i for i, (q, _) in enumerate(QUESTIONS) if ("ar" if is_ar(q) else "en") == lang]
    q3[idx] -= q3[idx].mean(axis=0)
score(d3, q3, "3. mean centering")
