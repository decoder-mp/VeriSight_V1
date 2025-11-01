# app.py
import streamlit as st
from bs4 import BeautifulSoup
import requests
import snscrape.modules.twitter as sntwitter
from sentence_transformers import SentenceTransformer, util
import spacy
from urllib.parse import quote, urlparse
import datetime
import os
from dotenv import load_dotenv

# -----------------------
# Load environment variables
# -----------------------
load_dotenv()
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN")  # For future Twitter API v2

# -----------------------
# Load models
# -----------------------
nlp = spacy.load("en_core_web_sm")
sbert = SentenceTransformer('all-MiniLM-L6-v2')

# -----------------------
# Trusted sources
# -----------------------
TRUSTED_DOMAINS = {"bbc.co.uk","bbc.com","cnn.com","theguardian.com","nation.africa","standardmedia.co.ke"}

# -----------------------
# Helper functions
# -----------------------
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
    except Exception:
        return []

def semantic_similarity(claim, candidates):
    if not candidates: return []
    claim_emb = sbert.encode(claim, convert_to_tensor=True)
    cand_embs = sbert.encode([c for c in candidates], convert_to_tensor=True)
    sims = util.pytorch_cos_sim(claim_emb, cand_embs)[0].cpu().numpy().tolist()
    return sims

def source_score_from_url(url):
    try:
        dom = urlparse(url).netloc.replace("www.","")
    except:
        return 0.35
    if any(d in dom for d in TRUSTED_DOMAINS): return 0.80
    if dom.endswith(".gov") or "police" in dom: return 0.90
    return 0.40

def aggregate_confidence(s_source, s_sim, s_time=1.0, s_media=0.8):
    return 0.35*s_source + 0.35*s_sim + 0.2*s_time + 0.1*s_media

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="VeriSight", layout="wide")

# Smaller title using markdown
st.markdown("<h2 style='text-align: left; font-size:28px;'>VeriSight — Fact & Deepfake Verification</h2>", unsafe_allow_html=True)

# Collapsible intro
with st.expander("Welcome! Click to read about VeriSight"):
    st.markdown("""
    **Welcome to VeriSight — Lightweight Fact & Media Verification!**  
    Verify claims, headlines, and media to detect misinformation or deepfakes.  
    Get quick insights from trusted sources and see how confident the verification is.  
    Paste a claim or upload media below to get started.
    """)

# -----------------------
# Sidebar (History)
# -----------------------
if 'history' not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("History")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history)):
            st.markdown(f"**{h['type'].capitalize()}** — {h['claim'][:50]}...")
            st.markdown(f"Confidence: {h['badge']} ({round(h['top_conf'],3)})")
            st.markdown("---")
    else:
        st.info("No history yet.")

# -----------------------
# Main verification interface
# -----------------------
st.subheader("Paste a claim or upload media below for verification.")

claim = st.text_area("Claim text", height=120)
uploaded_file = st.file_uploader("Upload your image/video for verification (optional)")

if st.button("Verify"):
    st.markdown("---")
    
    # -----------------------
    # Deepfake / Media Verification
    # -----------------------
    media_result = None
    if uploaded_file:
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post("http://127.0.0.1:5000/api/verify", files=files)
            if response.status_code == 200:
                media_result = response.json()
                st.success("Media verification successful!")
                st.write(media_result)
            else:
                st.error(f"Error verifying media: {response.json().get('error')}")
        except Exception as e:
            st.error(f"Media verification request failed: {str(e)}")

    # -----------------------
    # Claim verification
    # -----------------------
    if not claim.strip():
        st.warning("No claim text entered. Only media verification performed.")
        st.stop()
    
    with st.spinner("Normalising and searching..."):
        clean_claim, ents = normalize(claim)
        news = search_news_google_rss(clean_claim)
        cand_texts = [n["title"] for n in news]
        sims = semantic_similarity(clean_claim, cand_texts)

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

        if evidence:
            top = sorted(evidence, key=lambda x: x["conf"], reverse=True)[0]
            top_conf = top["conf"]
        else:
            top_conf = 0.0

        badge = "Low"
        if top_conf >= 0.75: badge="High"
        elif top_conf >= 0.5: badge="Medium"

    # -----------------------
    # Display results
    # -----------------------
    st.subheader("Verification Brief")
    st.markdown(f"**Claim:** {claim}")
    st.markdown(f"**Normalised:** {clean_claim}")
    st.markdown(f"**Entities detected:** {ents}")
    st.markdown(f"**Top confidence (badge):** {badge} ({round(top_conf,3)})")
    st.markdown("**Top evidence:**")
    if evidence:
        for ev in evidence[:6]:
            st.markdown(f"- {ev['title']} — {ev['link']} (sim={ev['sim']}, src={ev['src_score']})")
    else:
        st.write("No evidence found.")

    # Save to history
    st.session_state.history.append({
        "type": "claim",
        "claim": claim,
        "badge": badge,
        "top_conf": top_conf
    })
