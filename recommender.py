import numpy as np
#from sentence_transformers import SentenceTransformer
from paper import ArxivPaper
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

def rerank_paper(candidate:list[ArxivPaper], corpus:list[dict], key, url, model) -> list[ArxivPaper]:
    encoder = OpenAI(
        api_key=key,  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
        base_url=url  # 百炼服务的base_url
    )
    #sort corpus by date, from newest to oldest
    corpus = sorted(corpus,key=lambda x: datetime.strptime(x['data']['dateAdded'], '%Y-%m-%dT%H:%M:%SZ'),reverse=True)
    time_decay_weight = 1 / (1 + np.log10(np.arange(len(corpus)) + 1))
    time_decay_weight = time_decay_weight / time_decay_weight.sum()
    corpus_feature = np.zeros((len(corpus),1024))
    for num, paper in enumerate(corpus):
        corpus_feature[num] = encoder.embeddings.create(
            model=model,
            input=paper['data']['abstractNote'],
            dimensions=1024, # 指定向量维度（仅 text-embedding-v3及 text-embedding-v4支持该参数）
            encoding_format="float"
        ).data[0].embedding
    candidate_feature = np.zeros((len(candidate),1024))
    for num, paper in enumerate(candidate):
        candidate_feature[num] = encoder.embeddings.create(
            model=model,
            input=paper.summary,
            dimensions=1024, # 指定向量维度（仅 text-embedding-v3及 text-embedding-v4支持该参数）
            encoding_format="float"
        ).data[0].embedding
    #for s,c in zip(scores,candidate):
    #    c.score = s.item()
    #candidate = sorted(candidate,key=lambda x: x.score,reverse=True)
    #return candidate

    sim = cosine_similarity( candidate_feature,corpus_feature,)
    #sim = encoder.similarity(candidate_feature,corpus_feature) # [n_candidate, n_corpus]
    #scores = (sim * time_decay_weight).sum(axis=1) * 10 # [n_candidate]
    scores = np.partition(sim * time_decay_weight,-10,axis=1)[:,-10:].sum(1)
    for s,c in zip(scores,candidate):
        c.score = s.item()
    candidate = sorted(candidate,key=lambda x: x.score,reverse=True)
    return candidate