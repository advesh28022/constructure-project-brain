from rag import answer_with_rag
import json

TEST_CASES = [
    {
        "id": 1,
        "query": "What is the high-level goal of this project?",
        "expected_keywords": ["project brain", "construction", "documents"],
    },
    {
        "id": 2,
        "query": "Which backend framework is required?",
        "expected_keywords": ["fastapi"],
    },
    {
        "id": 3,
        "query": "Which frontend frameworks are allowed?",
        "expected_keywords": ["react", "next"],
    },
    {
        "id": 4,
        "query": "Name one structured extraction example they mention.",
        "expected_keywords": ["door schedule", "room", "mep"],
    },
    {
        "id": 5,
        "query": "How long do we have to complete the assignment?",
        "expected_keywords": ["36"],
    },
]


def evaluate():
    results = []
    for case in TEST_CASES:
        answer, sources = answer_with_rag(case["query"])
        text_lower = answer.lower()
        hits = [kw for kw in case["expected_keywords"] if kw.lower() in text_lower]
        if len(hits) == len(case["expected_keywords"]):
            status = "looks correct"
        elif hits:
            status = "partially correct"
        else:
            status = "wrong/uncertain"
        results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "answer_snippet": answer[:300],
                "hits": hits,
                "status": status,
                "sources": sources,
            }
        )
    return results


if __name__ == "__main__":
    res = evaluate()
    print(json.dumps(res, indent=2))
