# app.py
import streamlit as st
from bs4 import BeautifulSoup
import requests
import snscrape.modules.twitter as sntwitter
from sentence_transformers import SentenceTransformer, util
import spacy
from urllib.parse import quote, urlparse
import datetime

# Load models
nlp = spacy.load("en_core_web_sm")
sbert = SentenceTransformer('all-MiniLM-L6-v2')

# Helpers
TRUSTED_DOMAINS = {"bbc.co.uk","bbc.com","cnn.com","theguardian.com","nation.africa","standardmedia.co.ke"}

def normalize(text):
    doc = nlp(text)
    ents = [(ent.text, ent.label_) for ent in doc.ents]
    clean = " ".join([t.text for t in doc if not t.is_space])
    return clean, ents

def search_news_google_rss(query, limit=6):
    q = quote(query)
    url = f"https://news.google.com/rss/search?q={q}"
    try:
        resp = requests.get(url, timeout=8)
        soup = BeautifulSoup(resp.content, "xml")
        items = []
        for item in soup.find_all("item")[:limit]:
            items.append({
                "title": item.title.text,
                "link": item.link.text,
                "pubDate": item.pubDate.text
            })
        return items
    except Exception as e:
        return []
def search_tweets(query, limit=10):
    results = []
    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= limit: break
            results.append({
                "id": tweet.id,
                "user": tweet.user.username,
                "date": tweet.date,
                "content": tweet.content,
                "followers": tweet.user.followersCount,
                "account_created": tweet.user.created
            })
    except Exception as e:
        print(f"[WARN] Twitter search failed: {e}")
        return []  # gracefully return empty list
    return results


def source_score_from_url(url):
    try:
        dom = urlparse(url).netloc.replace("www.","")
    except:
        return 0.35
    if any(d in dom for d in TRUSTED_DOMAINS): return 0.80
    if dom.endswith(".gov") or "police" in dom: return 0.90
    return 0.40

def source_score_from_tweet(t):
    followers = t.get("followers",0)
    age_years = (datetime.datetime.now() - t.get("account_created", datetime.datetime.now())).days/365
    if followers>5000 and age_years>2: return 0.70
    if followers>100 and age_years>1: return 0.55
    return 0.25

def semantic_similarity(claim, candidates):
    if not candidates: return []
    claim_emb = sbert.encode(claim, convert_to_tensor=True)
    cand_embs = sbert.encode([c for c in candidates], convert_to_tensor=True)
    sims = util.pytorch_cos_sim(claim_emb, cand_embs)[0].cpu().numpy().tolist()
    return sims

def aggregate_confidence(s_source, s_sim, s_time=1.0, s_media=0.8):
    return 0.35*s_source + 0.35*s_sim + 0.2*s_time + 0.1*s_media

# Streamlit UI
st.set_page_config(page_title="VeriSight Lite", layout="wide")
st.title("VeriSight — Lightweight Fact Verification (MVP)")
st.markdown("Paste a claim (tweet or headline) and press *Verify*.")

claim = st.text_area("Claim text", height=120)
extra = st.text_input("Optional: URL of original post")
if st.button("Verify"):
    if not claim.strip():
        st.error("Please enter claim text.")
    else:
        with st.spinner("Normalising and searching..."):
            clean_claim, ents = normalize(claim)
            news = search_news_google_rss(clean_claim)
            tweets = search_tweets(clean_claim)
            # Prepare candidates text list
            cand_texts = [n["title"] for n in news] + [t["content"] for t in tweets]
            sims = semantic_similarity(clean_claim, cand_texts)
            # Build evidence table
            evidence = []
            idx = 0
            for n in news:
                s_sim = sims[idx] if idx < len(sims) else 0.0
                s_src = source_score_from_url(n["link"])
                conf = aggregate_confidence(s_src, s_sim)
                evidence.append({
                    "type":"news","title":n["title"],"link":n["link"],"pubDate":n["pubDate"],
                    "sim":round(s_sim,3),"src_score":round(s_src,2),"conf":round(conf,3)
                })
                idx+=1
            for t in tweets:
                s_sim = sims[idx] if idx < len(sims) else 0.0
                s_src = source_score_from_tweet(t)
                conf = aggregate_confidence(s_src, s_sim)
                evidence.append({
                    "type":"tweet","user":t["user"],"date":str(t["date"]),
                    "content":t["content"],"sim":round(s_sim,3),"src_score":round(s_src,2),"conf":round(conf,3)
                })
                idx+=1
            # Determine top evidence
            if evidence:
                top = sorted(evidence, key=lambda x: x["conf"], reverse=True)[0]
                top_conf = top["conf"]
            else:
                top_conf = 0.0
            # Map to badge
            badge = "Low"
            if top_conf >= 0.75: badge="High"
            elif top_conf >= 0.5: badge="Medium"
        # Render brief
        st.subheader("Verification Brief")
        st.markdown(f"**Claim:** {claim}")
        st.markdown(f"**Normalised:** {clean_claim}")
        st.markdown(f"**Entities detected:** {ents}")
        st.markdown(f"**Top confidence (badge):** **{badge}** ({round(top_conf,3)})")
        st.markdown("**Top evidence (sample):**")
        if evidence:
            for ev in evidence[:6]:
                if ev["type"]=="news":
                    st.write(f"- [News] {ev['title']} — {ev['link']} (sim={ev['sim']}, src={ev['src_score']})")
                else:
                    st.write(f"- [Tweet] @{ev['user']} {ev['content'][:120]}... (sim={ev['sim']}, src={ev['src_score']})")
        else:
            st.write("No evidence found.")
        st.markdown("---")
        st.markdown("**Recommended Action:**")
        if badge=="High":
            st.success("Likely true — monitor & consider reporting to relevant desk.")
        elif badge=="Medium":
            st.info("Unclear — seek human verification and look for more sources.")
        else:
            st.warning("Low confidence — withhold publication; request more evidence.")
