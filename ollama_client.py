
import json
import requests

from config import (
    OLLAMA_URL, MODEL, TEMPERATURE, MAX_TOKENS
)
#from prompts import SYSTEM_PROMPT, RESPONSE_SCHEMA
from prompts import load_prompt, load_md04_prompt, RESPONSE_SCHEMA

# Meghatározza a felhasználói parancsot és a hozzá tartozó SAP tranzakciót az Ollama AI segítségével.
def understand_command(user_text):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": load_prompt()},
                {"role": "user", "content": user_text}
            ],
            "format": RESPONSE_SCHEMA,
            "stream": False,
            "think": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            }
        },
        timeout=60
    )

    response.raise_for_status()
    result = response.json()

    print("\n--- Ollama teljesítmény ---")
    for key, label in [
        ("total_duration", "Összes idő"),
        ("load_duration", "Modell betöltése"),
        ("prompt_eval_duration", "Prompt feldolgozása"),
        ("eval_duration", "Válasz generálása")
    ]:
        print(f"{label}: {result.get(key, 0) / 1e9:.2f} mp")

    print(f"Generált tokenek: {result.get('eval_count', 0)}")

    data = json.loads(result["message"]["content"])
    return data

#Megválaszolja a felhasználó kérdését az MD04 összesítés alapján az Ollama AI segítségével.
def answer_md04(question, summary):

    messages = [
        {
            "role": "system",
            "content": load_md04_prompt()
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"SAP MD04 data:\n"
                f"{json.dumps(summary, ensure_ascii=False)}"
            )
        }
    ]

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": 200
            }
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()["message"]["content"].strip()