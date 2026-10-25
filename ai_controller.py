from config import ALLOWED
from ollama_client import understand_command, answer_md04
from sap_actions import open_transaction, display_md04, summarize_md04


def process_command(command: str) -> str:
    """A konzol és a webes chat közös SAP-feldolgozója."""
    result = understand_command(command)
    print("AI által felismert paraméterek:", result)
    tcode = result.get("tcode")

    if tcode not in ALLOWED:
        return "Nem felismert vagy nem támogatott művelet."

    if tcode == "MD04":
        material = result.get("material")
        plant = result.get("plant")
        if not material or not plant:
            return "Az MD04 lekérdezéshez anyagszám és gyár szükséges."
        #data = display_md04(material, plant)
        #summary = summarize_md04(data, result.get("period", "all"))

        data = display_md04(material, plant)

#Debugging output for MD04 data
        import json

        data = display_md04(material, plant)

        print("\n--- MD04 JSON DEBUG ---")
        print("Rekordok száma:", len(data["records"]))
        print(json.dumps(data, indent=2, ensure_ascii=False))
#Debugging output for MD04 summary

        answer = answer_md04(command, data)

        return answer

    return str(open_transaction(tcode))


def main():
    while True:
        command = input("\nSAP utasítás (exit = kilépés): ").strip()
        if command.lower() == "exit":
            break
        if not command:
            continue
        try:
            print(process_command(command))
        except Exception as error:
            print(f"Hiba: {error}")


if __name__ == "__main__":
    main()
