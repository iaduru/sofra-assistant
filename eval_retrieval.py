import json
import os
from sofra import config
from sofra.data.kb_retrieval import KBRetriever

EVAL_PATH = os.path.join("data", "eval_questions.jsonl")

def run_evaluation() -> None:
    kb = KBRetriever(config.KB_PATH)

    total_questions = 0
    hits_at_5 = 0

    print("Evaluating Knowledge Base Retrieval Accuracy (Recall@5)...\n")
    print("-" * 50)

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)

            if record.get("type") == "retrieval" and record.get("answerable") is True:
                total_questions += 1
                query = record["q"]
                expected_ids = set(record["expected_doc_ids"])

                results = kb.search(query, top_k=5)
                retrieved_ids = [doc["id"] for doc in results]

                hit = any(expected_id in retrieved_ids for expected_id in expected_ids)

                if hit:
                    hits_at_5 += 1
                else:
                    print(f"[MISS] Question id: {record['id']}")
                    print(f"Question: {query}")
                    print(f"Expected: {expected_ids}")
                    print(f"Retrieved:  {retrieved_ids}\n")

    print("-" * 50)
    print("EVALUATION RESULTS")
    print("-" * 50)
    print(f"Total Evaluated Questions : {total_questions}")
    print(f"Successful Retrievals     : {hits_at_5}")

    if total_questions > 0:
        accuracy = (hits_at_5 / total_questions) * 100
        print(f"Recall@5 Score            : {accuracy:.2f}%\n")

if __name__ == "__main__":
    run_evaluation()