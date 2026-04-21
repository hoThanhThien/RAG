from app.services.rag_service import build_vector_store


if __name__ == "__main__":
    result = build_vector_store(force=True)
    print("RAG index build result:")
    for key, value in result.items():
        print(f"- {key}: {value}")
