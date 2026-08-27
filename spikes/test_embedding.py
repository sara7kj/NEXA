from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("intfloat/multilingual-e5-small")

ar = "query: كم عدد أيام الإجازة السنوية؟"
en = "query: How many annual leave days do employees get?"
xx = "query: What is the office wifi password?"

emb = model.encode([ar, en, xx])

print("AR vs EN (same meaning):", round(float(util.cos_sim(emb[0], emb[1])), 4))
print("AR vs unrelated        :", round(float(util.cos_sim(emb[0], emb[2])), 4))
