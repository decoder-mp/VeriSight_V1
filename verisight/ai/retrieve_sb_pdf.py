# retrieve_sb_pdf.py
from sentence_transformers import SentenceTransformer, util
import json
import argparse

MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def load_corpus(path):
    # corpus should be JSONL with {"id":..., "text": ...}
    corpus = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            corpus.append(json.loads(line))
    return corpus

def encode_corpus(corpus, model):
    texts = [c["text"] for c in corpus]
    emb = model.encode(texts, convert_to_tensor=True)
    return emb

def retrieve(claim, corpus, corpus_emb, model, top_k=5):
    q_emb = model.encode(claim, convert_to_tensor=True)
    hits = util.semantic_search(q_emb, corpus_emb, top_k=top_k)[0]
    results = []
    for h in hits:
        idx = h['corpus_id']
        score = h['score']
        results.append({"id": corpus[idx]["id"], "text": corpus[idx]["text"], "score": float(score)})
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="corpus.jsonl")
    parser.add_argument("--claim", required=True)
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    model = SentenceTransformer(MODEL)
    corpus = load_corpus(args.corpus)
    emb = encode_corpus(corpus, model)
    res = retrieve(args.claim, corpus, emb, model, top_k=args.topk)
    print(res)
