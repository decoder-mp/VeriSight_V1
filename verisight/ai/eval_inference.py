# eval_inference.py
import sys
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch


MODEL_DIR = "fever-roberta-final"



# simple inference


def infer(claim, evidence_text):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    inputs = tokenizer(claim, evidence_text, truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    pred = torch.argmax(logits, dim=-1).item()
    return pred, logits.softmax(dim=-1).cpu().numpy().tolist()[0]

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python eval_inference.py \"claim text\" \"evidence text\"")
        sys.exit(1)
    claim = sys.argv[1]
    evidence = sys.argv[2]
    pred, probs = infer(claim, evidence)
    LABELS = {0: "SUPPORTS", 1: "REFUTES", 2: "NOT ENOUGH INFO"}
    print("Prediction:", LABELS[pred], "Probs:", probs)
