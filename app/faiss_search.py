def search(index, query, k=3):
    results = index.similarity_search_with_score(query, k=k)
    for i, (doc, score) in enumerate(results, 1):
        print(f"Rank {i} | Score: {score:.4f}")
        print(f"Source: {doc.metadata.get('source')} | Page: {doc.metadata.get('page', 'N/A')}")
        print(doc.page_content[:300])
        print("-" * 50)
    return results
