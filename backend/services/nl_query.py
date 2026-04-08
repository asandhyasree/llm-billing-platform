"""
Natural language → SQL → answer.

Converts a plain English question into a PostgreSQL SELECT query, executes it
against the usage ledger, and returns both the raw data and a human-readable answer.
"""
from sqlalchemy import text
from services import llm_client

_SCHEMA = """
PostgreSQL database. Table: usage_events
Columns:
  - tenant_id (VARCHAR): client identifier
  - model (VARCHAR): LLM model name, e.g. "gpt-4o", "claude-sonnet-4-6"
  - provider (VARCHAR): "openai", "anthropic", or "gemini"
  - input_tokens (INTEGER): tokens in the prompt
  - output_tokens (INTEGER): tokens in the response
  - total_cost_usd (DOUBLE PRECISION): cost at provider rate
  - billed_cost_usd (DOUBLE PRECISION): cost after markup
  - ts (TIMESTAMP): event timestamp
"""


async def nl_to_sql_to_answer(
    question: str,
    tenant_id: str,
    db,
) -> dict:
    # Step 1: Generate SQL from natural language
    sql_prompt = f"""Convert the following question into a valid PostgreSQL SELECT query.

Schema:
{_SCHEMA}

Rules:
- Always include WHERE tenant_id = '{tenant_id}'
- Use to_char(ts, 'YYYY-MM-DD') for date grouping
- Return ONLY the SQL query. No explanation, no markdown, no backticks.

Question: {question}"""

    sql = (await llm_client.complete(sql_prompt)).strip()

    # Step 2: Execute the generated SQL
    try:
        result_proxy = db.execute(text(sql))
        columns = list(result_proxy.keys())
        rows = [dict(zip(columns, row)) for row in result_proxy.fetchall()]
    except Exception as exc:
        return {"error": str(exc), "sql": sql, "question": question}

    # Step 3: Narrate the results in plain English
    answer_prompt = f"""A user asked: "{question}"

The data returned:
{rows[:20]}

Answer the question in one clear, direct sentence using only the data above.
If the data is empty, say "No data found for that query." """

    answer = await llm_client.complete(answer_prompt)

    return {
        "question": question,
        "sql":      sql,
        "rows":     rows,
        "answer":   answer,
    }
