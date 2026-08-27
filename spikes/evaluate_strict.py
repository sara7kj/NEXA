from sentence_transformers import SentenceTransformer, util
from dataset import DOCS, QUESTIONS

def is_ar(t):
    return any("\u0600" <= c <= "\u06FF" for c in t)

model = SentenceTransformer("intfloat/multilingual-e5-large")
keys = list(DOCS.keys())
doc_emb = model.encode(["passage: " + DOCS[k] for k in keys])

r1 = r3 = same_lang = 0

for q, expected in QUESTIONS:
    q_lang = "ar" if is_ar(q) else "en"
    q_emb = model.encode("query: " + q)
    scores = util.cos_sim(q_emb, doc_emb)[0]
    ranked = [keys[i] for i in scores.argsort(descending=True)]
    top1 = ranked[0]

    r1 += expected == top1
    r3 += expected in ranked[:3]
    top1_lang = "ar" if is_ar(DOCS[top1]) else "en"
    same_lang += top1_lang == q_lang

    mark = "OK  " if expected == top1 else "MISS"
    print(f"[{mark}] {q_lang} | want={expected:<12} got={top1}")

n = len(QUESTIONS)
print()
print(f"Recall@1        = {r1}/{n} = {r1/n:.2f}")
print(f"Recall@3        = {r3}/{n} = {r3/n:.2f}")
print(f"Same-lang bias  = {same_lang}/{n} = {same_lang/n:.2f}   (0.50 = neutral)")
