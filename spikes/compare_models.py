from sentence_transformers import SentenceTransformer, util

ar = "query: كم عدد أيام الإجازة السنوية؟"
en = "query: How many annual leave days do employees get?"
xx = "query: What is the office wifi password?"

for name in ["intfloat/multilingual-e5-small", "intfloat/multilingual-e5-large"]:
    model = SentenceTransformer(name)
    emb = model.encode([ar, en, xx])
    match = float(util.cos_sim(emb[0], emb[1]))
    noise = float(util.cos_sim(emb[0], emb[2]))
    print(f"{name.split('/')[-1]:<28} match={match:.4f}  noise={noise:.4f}  gap={match-noise:.4f}")
