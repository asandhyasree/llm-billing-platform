"""
RAG cost advisor.

When an anomaly is detected, retrieves similar resolved anomalies from ChromaDB
and uses them as context to generate a plain English explanation via an LLM.
"""
import chromadb
from sentence_transformers import SentenceTransformer

_embedder   = SentenceTransformer("all-MiniLM-L6-v2")
_chroma     = chromadb.Client()
_collection = _chroma.get_or_create_collection("anomaly_history")


def index_anomaly(anomaly: dict) -> None:
    """Store a resolved anomaly so it can be retrieved for future explanations."""
    text = (
        f"Tenant {anomaly['tenant_id']} had a {anomaly['deviation_pct']}% spike "
        f"on {anomaly['date']} using {anomaly['model']}. "
        f"Cause: {anomaly.get('resolved_cause', 'unknown')}."
    )
    _collection.add(
        documents=[text],
        embeddings=[_embedder.encode(text).tolist()],
        ids=[anomaly["id"]],
    )


async def explain_anomaly(anomaly: dict, llm_client) -> str:
    """
    Retrieve similar past anomalies and generate a plain English explanation
    with an actionable recommendation.
    """
    query = (
        f"{anomaly['deviation_pct']}% cost spike using {anomaly['model']} "
        f"on {anomaly['date']}"
    )
    query_embedding = _embedder.encode(query).tolist()
    results = _collection.query(query_embeddings=[query_embedding], n_results=3)
    similar_cases = (
        "\n".join(results["documents"][0])
        if results["documents"]
        else "No similar cases found."
    )

    prompt = f"""You are a cost advisor for LLM API usage.

A client had an unusually expensive day:
- Date: {anomaly['date']}
- Cost: ${anomaly['total_cost']:.4f} ({anomaly['deviation_pct']}% above their 30-day average)
- Primary model: {anomaly['model']}
- Input tokens: {anomaly['input_tokens']:,}
- Output tokens: {anomaly['output_tokens']:,}

Similar past anomalies from other clients:
{similar_cases}

In 2–3 sentences: explain the most likely cause of this spike, and give one specific recommendation.
Be direct and non-technical. Do not repeat the numbers back."""

    return await llm_client.complete(prompt)
