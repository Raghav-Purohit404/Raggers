import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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
