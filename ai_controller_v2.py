import json

from config import ALLOWED
from ollama_client import understand_command, answer_md04
from sap_actions import open_transaction, display_md04, summarize_md04

def main():
    while True:
        command = input("\nSAP utasítás (exit = kilépés): ").strip()

        if command.lower() == "exit":
            break

        if not command:
            continue

        try:
            #tcode = understand_command(command)
            result = understand_command(command)
            tcode = result["tcode"]

            print("Felismert paraméterek:", result)

            if tcode not in ALLOWED:
                print("Nem felismert vagy nem támogatott művelet.")
                continue

            print(f"AI döntés: {tcode} – {ALLOWED[tcode]}")

            if tcode == "MD04" and result["material"] and result["plant"]:
                # SAP MD04 adatok lekérdezése
                data = display_md04(result["material"], result["plant"])
                # Python aggregálás
                summary = summarize_md04(data)
                print("\nSAP összesítés:")
                print(json.dumps(summary, indent=2, ensure_ascii=False))
                # AI válaszgenerálás
                answer = answer_md04(command, summary)
                print("\nAI válasz:")
                print(answer)
            elif tcode == "MD04":
                print("Az MD04 lekérdezéshez anyagszám és gyár szükséges.")
            else:
                print(open_transaction(tcode))
                
            #open_transaction(tcode)
            #confirm = input("Végrehajtás? (i/n): ").strip().lower()

            #if confirm == "i":
            #    print(open_transaction(tcode))

        except Exception as error:
            print(f"Hiba: {error}")


if __name__ == "__main__":
    main()
