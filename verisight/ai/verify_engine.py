# verisight/ai/verify_engine.py
from bs4 import BeautifulSoup
import sys, json

def analyze_text(text):
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text()
    return {"authenticity_score": 0.5, "summary": clean[:200]}

if __name__ == "__main__":
    data = sys.stdin.read() or "<p>test</p>"
    print(json.dumps(analyze_text(data)))
