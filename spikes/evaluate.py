from sentence_transformers import SentenceTransformer, util
from dataset import DOCS, QUESTIONS

model = SentenceTransformer("intfloat/multilingual-e5-large")

keys = list(DOCS.keys())
doc_emb = model.encode(["passage: " + DOCS[k] for k in keys])

hits = {"ar": [0, 0], "en": [0, 0]}

for q, expected in QUESTIONS:
    lang = "ar" if any("\u0600" <= c <= "\u06FF" for c in q) else "en"
    q_emb = model.encode("query: " + q)
    scores = util.cos_sim(q_emb, doc_emb)[0]
    top3 = [keys[i] for i in scores.argsort(descending=True)[:3]]
    ok = expected in top3
    hits[lang][1] += 1
    hits[lang][0] += 1 if ok else 0
    print(f"[{'OK ' if ok else 'MISS'}] {q[:45]:<47} -> {top3[0]}")

print()
for lang in ("ar", "en"):
    h, t = hits[lang]
    print(f"Recall@3 [{lang}] = {h}/{t} = {h/t:.2f}")
total_h = hits['ar'][0] + hits['en'][0]
print(f"Recall@3 [all] = {total_h}/10 = {total_h/10:.2f}")
