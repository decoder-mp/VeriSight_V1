# train_fever.py
import os
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from preprocess import prepare_fever_split
import torch
from transformers import TrainingArguments


MODEL_NAME = os.getenv("MODEL_NAME", "roberta-base")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "fever-roberta")
MAX_LEN = int(os.getenv("MAX_LEN", 256))


def tokenize_batch(batch, tokenizer):
    # Ensure claim and evidence are text
    claims = [str(c) if c is not None else "" for c in batch["claim"]]
    evidences = []

    for e in batch["evidence"]:
        if isinstance(e, list):
            # Flatten if nested (some FEVER entries use lists of lists)
            if len(e) > 0 and isinstance(e[0], list):
                flat = " ".join([" ".join(inner) for inner in e])
            else:
                flat = " ".join(map(str, e))
            evidences.append(flat)
        elif e is None:
            evidences.append("")
        else:
            evidences.append(str(e))

    return tokenizer(claims, evidences, truncation=True, max_length=MAX_LEN)

def main():
    print("Loading tokenizer and model:", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)

    # Prepare datasets
    print("Loading FEVER train / validation via helper")
    train_ds = prepare_fever_split("train")
    val_ds = prepare_fever_split("validation")

    # Filter out examples without labels (if any)
    train_ds = train_ds.filter(lambda x: x["label"] is not None)
    val_ds = val_ds.filter(lambda x: x["label"] is not None)

    # Tokenize
    print("Tokenizing datasets")
    train_tok = train_ds.map(lambda b: tokenize_batch(b, tokenizer), batched=True, remove_columns=train_ds.column_names)
    val_tok = val_ds.map(lambda b: tokenize_batch(b, tokenizer), batched=True, remove_columns=val_ds.column_names)

    train_tok.set_format(type="torch")
    val_tok.set_format(type="torch")


    training_args = TrainingArguments(
        output_dir="./fever-roberta-final",
        evaluation_strategy="epoch",       # Evaluate every epoch
        save_strategy="epoch",             # Save model every epoch
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        load_best_model_at_end=True,       # Keep the best model
        metric_for_best_model="accuracy",  # Optional, if you define a compute_metrics fn
        logging_dir="./logs",
        logging_strategy="epoch",          # Log metrics every epoch
        save_total_limit=2,                # Keep last 2 checkpoints
    )

    def compute_metrics(eval_pred):
        import evaluate
        metric_acc = evaluate.load("accuracy")
        logits, labels = eval_pred
        preds = logits.argmax(axis=-1)
        return metric_acc.compute(predictions=preds, references=labels)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tok,
        eval_dataset=val_tok,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    print("Model saved to", OUTPUT_DIR)
    trainer.save_model("fever-roberta-final")
    
if __name__ == "__main__":
    main()


