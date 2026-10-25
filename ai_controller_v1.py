
import json
import requests
from sap_action import open_transaction

MODEL = "qwen3:1.7b"

ALLOWED = {
    "MM03": "Anyagtörzs megjelenítés",
    "VA03": "Vevői rendelés megjelenítés",
    "MD04": "Készlet igény lista"
}


def understand_command(user_text):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                            "You are an SAP GUI command classifier. "
                            "Understand Hungarian and English SAP terminology. "
                            "Return only the JSON object required by the schema. "
                            "Allowed transactions: MM03, VA03, MD04. "
                            "If the request is unclear or unsupported, return NONE. "
                            "Never guess an unrelated transaction. "
                            "Extract material number and plant if provided. "
                            "Do not invent missing values. Use null if not specified. "
                            "Preserve material numbers exactly as written. "
                            "Example: 'Show MD04 for ZPDS-MOTOR-A in plant 2140' "
                            "-> {\"tcode\":\"MD04\",\"material\":\"ZPDS-MOTOR-A\",\"plant\":\"2140\"}. "

                            "Examples: "
                            "'Show material master' -> MM03; "
                            "'Anyagtörzs megjelenítése' -> MM03; "
                            "'Show sales order' -> VA03; "
                            "'Vevői rendelés megjelenítése' -> VA03; "
                            "'Stock requirements list' -> MD04; "
                            "'Készletigény lista' -> MD04; "
                            "'Mutasd meg a cikkszám készletigényeit' -> MD04; "
                            "'Display stock requirements' -> MD04; "
                            "'Create purchase order' -> NONE. "
                    )
                },
                {"role": "user", "content": user_text}
            ],
            
            "format": {
                "type": "object",
                "properties": {
                    "tcode": {
                        "type": "string",
                        "enum": ["MM03", "VA03", "MD04", "NONE"]
                    },
                    "material": {
                        "type": ["string", "null"]
                    },
                    "plant": {
                        "type": ["string", "null"]
                    }
                },
                "required": ["tcode", "material", "plant"],
                "additionalProperties": False
            },

            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": 30
                }
        },
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    print("\n--- Ollama teljesítmény ---")
    print(f"Összes idő: {result['total_duration'] / 1e9:.2f} mp")
    print(f"Modell betöltése: {result['load_duration'] / 1e9:.2f} mp")
    print(f"Prompt feldolgozása: {result['prompt_eval_duration'] / 1e9:.2f} mp")
    print(f"Válasz generálása: {result['eval_duration'] / 1e9:.2f} mp")
    print(f"Generált tokenek: {result['eval_count']}")


    data = json.loads(response.json()["message"]["content"])
    #return data["tcode"]
    return data


while True:
    command = input("\nSAP utasítás (exit = kilépés): ").strip()

    if command.lower() == "exit":
        break

    try:
        #tcode = understand_command(command)
        result = understand_command(command)
        tcode = result["tcode"]

        print("Felismert paraméterek:", result)

        if tcode not in ALLOWED:
            print("Nem felismert vagy nem támogatott művelet.")
            continue

        print(f"AI döntés: {tcode} – {ALLOWED[tcode]}")
        open_transaction(tcode)
        #confirm = input("Végrehajtás? (i/n): ").strip().lower()

        #if confirm == "i":
        #    print(open_transaction(tcode))

    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Hiba: {error}")
