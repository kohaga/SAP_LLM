import json
import requests
from sap_actions import display_md04, summarize_md04

# 1. SAP adatok lekérdezése
data = display_md04("ZPDS-MOTOR-A", "2140")

# 2. Python aggregálás
summary = summarize_md04(data)

print("Python összesítés:")
print(json.dumps(summary, indent=2, ensure_ascii=False))

# 3. Felhasználói kérdés
# question = (
#     "Mennyi az összes igény és beérkezés, "
#     "valamint az induló és záró készlet?"
# )
question = input("Mit szeretnél tudni az anyagról? ")

# 4. Ollama prompt
prompt = f"""
You are an SAP MRP reporting assistant.
Answer the user's question in Hungarian.

Rules:
- Use ONLY the values provided in the JSON.
- Do NOT perform any calculations.
- Do NOT add or subtract the values.
- Do NOT introduce additional metrics.
- Answer only what the user asked.
- Use a maximum of 3 short sentences.
- Express quantities as whole numbers when possible.
- closing_available is projected available quantity,
  NOT physical warehouse stock.
- If total_demand equals total_receipts and opening_stock
  equals closing_available, state that planned receipts
  cover the total demand in quantity.
- For stock shortage questions, use shortage_detected.
- If shortage_detected is false, clearly state that
  no negative projected available quantity was detected.
- If shortage_detected is true, report shortage_dates.
- Never infer stock shortage from opening_stock
  or closing_available alone.
- Never make contradictory statements.

Question:
{question}

SAP data:
{json.dumps(summary, ensure_ascii=False)}
"""

# 5. Ollama meghívása
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3:1.7b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    },
    timeout=120
)

response.raise_for_status()

print("\nAI válasz:\n")
print(response.json()["response"])