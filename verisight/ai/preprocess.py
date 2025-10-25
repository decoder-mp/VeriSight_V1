import json
import os
from datasets import Dataset

def prepare_fever_split(split):
    local_path = f"data/fever.{split}.jsonl"
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local FEVER file not found: {local_path}")

    print(f"📘 Loading FEVER data locally from {local_path}")
    with open(local_path, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    # FEVER format keys: claim, evidence, label
    examples = []
    for item in data:
        claim = item.get("claim")
        label = item.get("label", "NOT ENOUGH INFO")
        # Extract only first evidence sentence (simplified)
        if item.get("evidence"):
            try:
                first_evidence = item["evidence"][0][0][2]  # [evidence_set][sentence_tuple][sentence_text]
            except Exception:
                first_evidence = ""
        else:
            first_evidence = ""
        examples.append({"claim": claim, "evidence": first_evidence, "label": label})

    # Convert labels to numeric
    label_map = {"SUPPORTS": 0, "REFUTES": 1, "NOT ENOUGH INFO": 2}
    for ex in examples:
        ex["label"] = label_map.get(ex["label"], 2)

    return Dataset.from_list(examples)
