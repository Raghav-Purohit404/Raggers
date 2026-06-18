import argparse
import json
import sys

from runtime_paths import ensure_runtime_environment

ensure_runtime_environment()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True)
    args = parser.parse_args()

    from engine.app.retriever import query_rag

    result = query_rag(args.query)

    print(json.dumps({
        "query": args.query,
        "answer": result
    }))

if __name__ == "__main__":
    main()
